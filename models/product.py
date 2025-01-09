# -*- coding:utf-8 -*-

from models.base import TimestampMixin
from tortoise import fields


class Product(TimestampMixin):

    real_price = fields.IntField(null=False, description='实价，以分为单位')
    origin_price = fields.IntField(null=False, description='原价，以分为单位')
    minute = fields.IntField(null=False, description='分钟数')
    description = fields.CharField(null=True, max_length=255, description='描述')
    sell_count = fields.IntField(null=False, default=0, description='销量')
    status = fields.IntField(null=False, default=0, description='上线状态')
    thumb = fields.CharField(null=True, max_length=255, description='图片地址')
    buy_limit = fields.IntField(null=False, default=1, description='每人限购数量')

    class Meta:
        table_description = "售卖产品包"
        table = "product"


class AccountRecord(TimestampMixin):

    rest_minute = fields.IntField(null=False, description='剩余分钟数')
    change_minute = fields.IntField(null=False, description='消费或者充值的分钟数， 正数表示充值，负数表示消费')
    source = fields.IntField(null=False, description='变动来源，1->消费， 2->充值')
    user = fields.ForeignKeyField('base.User', related_name='account_record')

    class Meta:
        table_description = "账户变动记录"
        table = "account_record"


class Order(TimestampMixin):
    trade_no = fields.CharField(null=False, max_length=40, description='订单号')
    product_num = fields.IntField(null=False, description='购买数量')
    pay_amount = fields.IntField(null=False, description='支付金额，以分为单位')
    status = fields.IntField(null=False, default=0, description='订单支付状态, 0->未支付， 1->已支付， 2->售后中，3->已退款')
    transaction_id = fields.CharField(null=True, max_length=40, description='微信端交易订单号')
    openid = fields.CharField(null=False, max_length=40, description='付款人openid')
    product = fields.ForeignKeyField('product.Product', related_name='orders')
    user = fields.ForeignKeyField('base.User', related_name='product_order', description='付款人id')
    car_info = fields.ForeignKeyField('tech_car.CarInfo', related_name='car_order', description='关联设备')
    field_provider = fields.ForeignKeyField('field_provider.FieldProvider', related_name='order_list',
                                            description='场地提供方')
    profit_percent = fields.IntField(null=False, default=0, description='分成比例')
    profit_amount = fields.IntField(null=False, default=0, description='分成金额')
    profit_status = fields.IntField(null=False, default=0,
                                    description='分成状态， 0->未支付，1->已支付，2->已申请，3->已批准，4->已打款， 5->已拒绝')

    class Meta:
        table_description = "订单记录"
        table = "product_order"
