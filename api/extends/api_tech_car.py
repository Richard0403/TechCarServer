import datetime
import time

import pytz
from fastapi import APIRouter, Security, Request, Depends

from core.Auth import check_permissions
from core.LatLngDistance import LatLngDistance
from core.Response import success, fail
from models.base import User
from models.tech_car import CarUseRecord, CarLocationRecord, CarGroup, CarInfo
from mqtt import mqtt_car
from schemas import base
from schemas.base import PageQuery, TradeNoQuery, GroupCarsQuery
from schemas.tech_car import UseRecordResp, ReturnCarParam, UseRecordLisResp, UseGroupResp, GroupCarsResp, ChangeBattery

router = APIRouter()


@router.get('/get/user_current_record', summary="获取用户当前正在使用的记录",
            response_model=UseRecordResp,
            dependencies=[Security(check_permissions)])
async def get_user_current_record(req: Request):
    user_id = req.state.user_id
    not_return_car = await (CarUseRecord.filter(user_info__id=user_id, status__in=[1, 3])
                            .prefetch_related('car_info', 'car_info__group')
                            .order_by("-create_time")
                            .first())
    if not_return_car:
        not_return_car.order_info = None
    # 获取当前页的数据列表
    return success(not_return_car)


@router.get('/get/use_record_by_trade_no', summary="通过订单号，获取使用记录",
            response_model=UseRecordResp,
            dependencies=[Security(check_permissions)])
async def get_record_by_trade_no(req: Request, query: TradeNoQuery = Depends()):
    user_id = req.state.user_id
    use_record = await (CarUseRecord.filter(user_info__id=user_id, order_info__trade_no=query.trade_no)
                        .prefetch_related('car_info', 'order_info')
                        .first())
    if use_record:
        use_record.order_info.product = None
        use_record.car_info.group = None
    return success(use_record)


@router.get('/use_records', summary="获取用户所有的使用记录",
            response_model=UseRecordLisResp,
            dependencies=[Security(check_permissions)])
async def get_user_use_records(req: Request, query: PageQuery = Depends()):
    user_id = req.state.user_id
    offset = (query.page - 1) * query.page_size
    use_records = await (CarUseRecord.filter(user_info__id=user_id)
                         .prefetch_related('car_info', 'car_info__group')
                         .order_by("-create_time")
                         .offset(offset)
                         .limit(query.page_size))
    for record in use_records:
        record.order_info = None
    return success(use_records)


@router.post('/return_car', summary="归还车辆",
             response_model=base.BaseResp,
             dependencies=[Security(check_permissions)])
async def return_car(req: Request, post: ReturnCarParam):
    user_id = req.state.user_id
    car_record = await (CarUseRecord.filter(id=post.use_record_id)
                        .prefetch_related('car_info', 'car_info__group')
                        .order_by("-create_time")
                        .first())
    if car_record.status == 1:
        # 使用中
        time_delta = datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai')) - car_record.begin_time
        # 剩余分钟数
        rest_minute = car_record.minute - int(time_delta.seconds / 60)
        if rest_minute < 0:
            # 时间已到， 检查位置后还车
            mqtt_car.get_car_location(car_record.car_info.device_id)
            time.sleep(2)
            permit_return, distance = await check_location_permit(car_record.car_info.id,
                                                                  car_record.car_info.group.latitude,
                                                                  car_record.car_info.group.longitude,
                                                                  car_record.car_info.group.return_distance)
            if permit_return:
                # 距离符合要求说明已经回来了，把超时的使用记录设置为已归还
                car_record.status = 2
                await CarUseRecord.save(car_record)
                # 更新电池电量
                mqtt_car.get_car_battery(car_record.car_info.device_id)
                return success(msg='车辆归还成功，感谢使用')
            else:
                return fail(msg=f'车辆距离还车点{int(distance)}米，请靠近一点重试吧')
            pass
        else:
            # 时间未到，提示时间未到，不可还车
            return fail(msg=f'车辆的时间还剩{rest_minute}分钟，再玩一会吧')
            pass
    elif car_record.status == 2:
        # 更新电池电量
        mqtt_car.get_car_battery(car_record.car_info.device_id)
        return success(msg='车辆归还成功，感谢使用')
    elif car_record.status == 3:
        mqtt_car.get_car_location(car_record.car_info.device_id)
        time.sleep(2)
        permit_return, distance = await check_location_permit(car_record.car_info.id,
                                                              car_record.car_info.group.latitude,
                                                              car_record.car_info.group.longitude,
                                                              car_record.car_info.group.return_distance)
        if permit_return:
            # 距离符合要求说明已经回来了，把超时的使用记录设置为已归还
            car_record.status = 2
            await CarUseRecord.save(car_record)
            # 更新电池电量
            mqtt_car.get_car_battery(car_record.car_info.device_id)
            return success(msg='车辆归还成功，感谢使用')
        else:
            return fail(msg=f'车辆距离还车点{int(distance)}米，请靠近一点重试吧')
    else:
        return fail(msg=f'车辆状态{car_record.status}未知，请联系客服')


@router.get('/get/user_charge_group', summary="获取用户管理的分组",
            response_model=UseGroupResp,
            dependencies=[Security(check_permissions)])
async def get_user_charge_group(req: Request):
    user_id = req.state.user_id
    group_list = await CarGroup.filter(charge_user__id=user_id)
    return success(group_list)


@router.get('/get/group_cars', summary="获取分组下的车辆",
            response_model=GroupCarsResp,
            dependencies=[Security(check_permissions)])
async def get_group_cars(req: Request, query: GroupCarsQuery = Depends()):
    car_list = await CarInfo.filter(group__id=query.group_id).prefetch_related('group')
    for car in car_list:
        last_location = await CarLocationRecord.filter(car_info__id=car.id).order_by('-create_time').first()
        car.last_location = last_location
    return success(car_list)


@router.post('/change_battery', summary="更换电池",
             response_model=base.BaseResp,
             dependencies=[Security(check_permissions)])
async def changeCarBattery(req: Request,  post: ChangeBattery):

    mqtt_car.get_car_battery(post.device_id)
    return success(msg='换电成功')

async def check_location_permit(car_info_id: int, group_latitude, grop_longitude, group_return_distance) -> (
        bool, float):
    latest_location = await (CarLocationRecord
                             .filter(car_info__id=car_info_id)
                             .order_by('-create_time')
                             .first())
    if latest_location:
        distance = (LatLngDistance(lat1=latest_location.latitude, lon1=latest_location.longitude,
                                   lat2=group_latitude,
                                   lon2=grop_longitude)
                    .calculate())
        return distance < group_return_distance, distance
    else:
        return False, 1000
