# -*- coding:utf-8 -*-


from models.base import TimestampMixin, User
from tortoise import fields

from models.field_provider import FieldProvider
from models.product import Order


class CarGroup(TimestampMixin):
    location = fields.CharField(null=True, max_length=255, description='详细位置描述')
    residential = fields.CharField(null=True, max_length=255, description='小区')
    latitude = fields.DecimalField(max_digits=18, decimal_places=14, description='纬度')  # 纬度
    longitude = fields.DecimalField(max_digits=18, decimal_places=14, description='精度')  # 经度
    adcode = fields.IntField(null=True, max_length=255, description='区域编码')
    return_distance = fields.IntField(null=False, default=50, description='最小还车距离')
    car_list = fields.ReverseRelation['CarInfo']
    charge_user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        'base.User', null=True, related_name='charge_group_list', on_delete=fields.SET_NULL
    )
    field_provider: fields.ForeignKeyRelation[FieldProvider] = fields.ForeignKeyField(
        'field_provider.FieldProvider', null=True, related_name='car_group_list', on_delete=fields.SET_NULL
    )

    class Meta:
        table_description = "小车分组"
        table = "car_group"


class CarInfo(TimestampMixin):
    price = fields.IntField(null=False, description='购买价格，以分为单位')
    image = fields.CharField(null=False, max_length=255, description='车辆图片')
    usage_image = fields.CharField(null=False, max_length=255, description='使用方式描述图片')
    device_id = fields.CharField(null=False, max_length=100, description='内置设备ID')
    battery_electric = fields.IntField(null=False, description='剩余电量')
    battery_charge_times = fields.IntField(null=False, default=0, description='电池充电次数')
    battery_latest_charge = fields.DatetimeField(null=True, description="电池上次充电时间")
    status = fields.IntField(null=False, default=0, description='车辆状态： 0->闲置， 1->使用中， 2->无法使用')
    group: fields.ForeignKeyRelation[CarGroup] = fields.ForeignKeyField(
        'tech_car.CarGroup', null=True, related_name='car_list', on_delete=fields.SET_NULL
    )
    use_records = fields.ReverseRelation['CarUseRecord']
    location_records = fields.ReverseRelation['CarLocationRecord']
    voltage = fields.IntField(null=False, default=0, description='电压')

    class Meta:
        table_description = "小车信息"
        table = "car_info"


class CarUseRecord(TimestampMixin):
    status = fields.IntField(null=False, default=0,
                             description='使用记录状态： 0->未开始使用， 1->使用中，2->已归还， 3->已超时未归还')
    begin_time = fields.DatetimeField(null=True, description="开始时间")
    end_time = fields.DatetimeField(null=True, description="结束时间")

    minute = fields.IntField(null=False, description='启用时长,分钟为单位')

    car_info: fields.ForeignKeyRelation[CarInfo] = fields.ForeignKeyField(
        'tech_car.CarInfo', related_name='car_info', on_delete=fields.CASCADE
    )
    user_info: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        'base.User', related_name='user_info', on_delete=fields.CASCADE
    )
    order_info: fields.ForeignKeyRelation[Order] = fields.ForeignKeyField(
        'product.Order', null=True, related_name='order_info', on_delete=fields.SET_NULL
    )

    class Meta:
        table_description = "小车使用记录"
        table = "car_use_record"


class CarLocationRecord(TimestampMixin):
    car_info: fields.ForeignKeyRelation[CarInfo] = fields.ForeignKeyField(
        'tech_car.CarInfo', related_name='location_records', on_delete=fields.CASCADE
    )
    latitude = fields.DecimalField(max_digits=18, decimal_places=14, description='纬度')  # 纬度
    longitude = fields.DecimalField(max_digits=18, decimal_places=14, description='精度')  # 经度
    gps_location = fields.BooleanField(default=False, description="是否使用gps定位")

    class Meta:
        table_description = "小车定位记录"
        table = "car_location_record"
