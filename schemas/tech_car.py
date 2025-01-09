# -*- coding:utf-8 -*-


from datetime import datetime
from pydantic import Field, BaseModel, validator
from typing import Optional, List
from schemas.base import BaseResp, ResAntTable
from schemas.order import ProductInfo, OrderInfo


class Group(BaseModel):
    id: int
    location: str
    residential: str
    latitude: float
    longitude: float
    adcode: int
    return_distance: int

    class Config:
        orm_mode = True


class CarLocationRecord(BaseModel):
    latitude: float
    longitude: float
    gps_location: bool

    class Config:
        orm_mode = True


class CarInfo(BaseModel):
    id: int
    price: int
    image: str
    usage_image: str
    device_id: str
    battery_electric: int
    battery_charge_times: int
    battery_latest_charge: datetime
    status: int
    group: Optional[Group]
    last_location: Optional[CarLocationRecord]
    voltage: int

    class Config:
        orm_mode = True


class CarUseRecord(BaseModel):
    id: int
    status: int
    begin_time: datetime
    end_time: Optional[datetime] = None
    minute: int
    car_info: Optional[CarInfo] = None
    order_info: Optional[OrderInfo] = None
    update_time: datetime
    create_time: datetime

    class Config:
        orm_mode = True


class UseRecordResp(BaseResp):
    data: Optional[CarUseRecord] = None


class UseGroupResp(BaseResp):
    data: Optional[List[Group]] = None


class UseRecordLisResp(BaseResp):
    data: Optional[List[CarUseRecord]]


class GroupCarsResp(BaseResp):
    data: Optional[List[CarInfo]] = None


class ReturnCarParam(BaseModel):
    use_record_id: str


class ChangeBattery(BaseModel):
    device_id: str
