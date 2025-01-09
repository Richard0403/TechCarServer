# -*- coding:utf-8 -*-

"""
 任务管理
"""
import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.LatLngDistance import LatLngDistance
from core.Logger import task_logger
from core.WeChatSubcribe import sendMinuteRestMsg
from models.tech_car import CarUseRecord, CarInfo, CarLocationRecord
from mqtt import mqtt_car


def startAsyncSchedulerTask():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_using_time_send_tips, 'interval', seconds=1 * 60)  # 检查正在使用的小车剩余时间
    scheduler.add_job(check_not_return_record, 'interval', seconds=1 * 60)  # 检查未归还订单的车辆（包含使用中和归还超时的）
    scheduler.add_job(check_battery, 'interval', seconds=15 * 60)  # 检查车辆电池
    scheduler.start()


async def check_using_time_send_tips():
    """
    检查正在进行中的小车使用时间, 剩余2分钟时发送尽快还车消息，一分钟检查一次
    """
    task_logger.info('执行任务 check_using_time')
    not_return_list = await CarUseRecord.filter(status=1).prefetch_related('user_info', 'car_info', 'user_info__wechat')
    for use_record in not_return_list:
        # 已耗时
        time_delta = datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai')) - use_record.begin_time
        # 剩余分钟数
        rest_minute = use_record.minute - int(time_delta.seconds / 60)
        if rest_minute >= 0:
            task_logger.info(f"用户剩余分钟数：{use_record.car_info.device_id}==={rest_minute}分钟")
            if rest_minute == 2 or rest_minute == 0:
                await sendMinuteRestMsg(use_record.user_info.wechat.openid, use_record.car_info.device_id,
                                        rest_minute)
        else:
            # 超时了，把使用记录设为超时
            use_record.status = 3
            await CarUseRecord.save(use_record)
            # 超时了，如果继电器关闭的消息，没有成功触发，就把使用的小车设置为闲置
            car_info = await CarInfo.filter(id=use_record.car_info.id).first()
            if car_info.status == 1:
                car_info.status = 0
                await CarInfo.save(car_info)
                task_logger.info(f"用户已超时，并且车辆正在使用中（概率比较低），把车辆设置为闲置："
                                 f"{use_record.car_info.device_id}，record_id==={use_record.id}")
    pass


async def check_not_return_record():
    """
    检查未归还订单的车辆（包含使用中和归还超时的）归还状态 一分钟一次， 如果位置符合还车点要求，则把借用此车未归还的的所有记录设为已归还
    """
    print('异步任务 check_return_status')
    not_return_list = await (CarUseRecord.filter(status__in=[1, 3])
                             .prefetch_related('user_info', 'car_info', 'car_info__group'))
    need_locate_car = []
    for use_record in not_return_list:
        # 未归还车辆的位置
        latest_location = await (CarLocationRecord
                                 .filter(car_info__id=use_record.car_info.id)
                                 .order_by('-create_time')
                                 .first())
        # 车辆去重，都进行一次定位，以免重复定位
        record_device_id = use_record.car_info.device_id
        if record_device_id not in need_locate_car:
            need_locate_car.append(record_device_id)
            mqtt_car.get_car_location(record_device_id)
        if latest_location:
            # 未归还车辆距离归还点的距离
            distance = (LatLngDistance(lat1=latest_location.latitude, lon1=latest_location.longitude,
                                       lat2=use_record.car_info.group.latitude,
                                       lon2=use_record.car_info.group.longitude)
                        .calculate())

            if distance < use_record.car_info.group.return_distance and use_record.status == 3:
                # 距离小于50说明已经回来了，把所有的超时的使用记录设置为已归还
                use_record.status = 2
                await CarUseRecord.save(use_record)
    pass


async def check_battery():
    car_list = await CarInfo.filter().all()
    for car in car_list:
        mqtt_car.get_car_battery(car.device_id)
    pass
