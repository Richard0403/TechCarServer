import datetime

from core.CoordTransformUtil import wgs84_to_gcj02
from core.LatLngDistance import LatLngDistance
from core.Logger import mqtt_logger
from core.WeChatSubcribe import sendMinuteRestMsg
from models.tech_car import CarLocationRecord, CarInfo, CarUseRecord


async def save_location(imei: str, lat: float, lng: float, gps: bool):
    """
    保存基站定位和gps定位
    """
    if lat != 0 and lng != 0:
        car_info = await CarInfo.filter(device_id=imei).first()
        if car_info:
            convert_lng, convert_lat = wgs84_to_gcj02(lng, lat)
            await CarLocationRecord.create(car_info=car_info, latitude=convert_lat,
                                           longitude=convert_lng, gps_location=gps)
            mqtt_logger.info(f"经纬度保存成功：{imei}")


async def start_use_car(imei: str):
    """
    车辆开始打开电源
    """
    # 更新车辆状态为使用中
    print("车辆打开电源" + imei)
    await CarInfo.filter(device_id=imei).update(status=1)
    # 更新使用记录的状态为使用中, 可能会出现一个场景，第一个人付钱之后，若因为网络问题没有成功启动车辆，第二个人付钱了，此时启动了车辆，会更新到第二个人的数据上，
    # 概率比较小，也比较符合常理， 第一个人可以申请退款
    car_use_record = await (CarUseRecord.filter(car_info__device_id=imei)
                            .prefetch_related('user_info')
                            .order_by('-create_time').first())
    car_use_record.status = 1
    car_use_record.begin_time = datetime.datetime.now()
    await CarUseRecord.save(car_use_record)
    mqtt_logger.info(f"打开车辆电源之后，保存车辆状态和使用记录状态成功：{imei}")
    # 如果是用完接着扫码启动， 可以把上次未归还的记录更改为已归还，因为这次车辆还是在他的名下
    last_not_return_record = await (CarUseRecord.filter(car_info__device_id=imei, status=3,
                                                        user_info__id=car_use_record.user_info.id)
                                    .order_by('-create_time').first())
    if last_not_return_record:
        last_not_return_record.status = 2
        await CarUseRecord.save(last_not_return_record)
        mqtt_logger.info(f"打开车辆电源之后，存在上次未归还使用记录：{last_not_return_record.id}, 状态置为2")


async def finish_use_car(imei: str):
    """
    车辆结束关闭电源
    """
    # 更新车辆状态为闲置
    print("车辆自动关闭电源" + imei)
    await CarInfo.filter(device_id=imei).update(status=0)
    car_info = await CarInfo.filter(device_id=imei).prefetch_related('group').first()
    car_loc = await CarLocationRecord.filter(car_info__id=car_info.id).order_by('-create_time').first()
    distance = (LatLngDistance(lat1=car_loc.latitude, lon1=car_loc.longitude,
                               lat2=car_info.group.latitude, lon2=car_info.group.longitude)
                .calculate())
    mqtt_logger.info(f"关闭车辆电源之后，计算车辆距离换车点位置：{imei}==={distance}")

    # 更新使用记录
    car_use_record = await (CarUseRecord.filter(car_info__device_id=imei)
                            .prefetch_related('user_info', 'user_info__wechat', 'car_info')
                            .order_by('-create_time').first())
    # 少于50米，归还成功，否则设为超时未归还
    car_use_record.status = 2 if distance < car_info.group.return_distance else 3
    car_use_record.end_time = datetime.datetime.now()
    await CarUseRecord.save(car_use_record)
    # 发送结束的消息
    await sendMinuteRestMsg(car_use_record.user_info.wechat.openid, car_use_record.car_info.device_id,
                            0)
    mqtt_logger.info(f"关闭车辆电源之后，保存车辆状态和使用记录状态成功：{imei}")


async def manual_close_car(imei: str):
    await CarInfo.filter(device_id=imei).update(status=0)


# 更新电池电压信息
async def refresh_car_battery(imei: str, battery: int):
    # 设置电压上下限
    min_voltage = 11.3  # 完全放电的电压
    max_voltage = 12.6  # 完全充满电的电压
    # 如果电压低于最小值，返回0%，如果高于最大值，返回100%
    if battery <= min_voltage:
        percentage = 0
    elif battery >= max_voltage:
        percentage = 100
    else:
        percentage = int((battery - min_voltage) / (max_voltage - min_voltage) * 100)
    await CarInfo.filter(device_id=imei).update(battery_electric=percentage, voltage=battery)
