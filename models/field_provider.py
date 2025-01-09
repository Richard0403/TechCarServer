from tortoise import fields

from models.base import TimestampMixin


class FieldProvider(TimestampMixin):
    name = fields.CharField(null=True, max_length=255, description='提供方名称')
    phone = fields.CharField(null=True, max_length=11, description='联系方式')
    charge_name = fields.CharField(null=True, max_length=255, description='负责人')
    location = fields.CharField(null=True, max_length=255, description='详细位置描述')
    profit_percent = fields.IntField(null=True, max_length=11, description='分成比例')
    profit_card = fields.CharField(null=True, max_length=255, description='分成打款账号')
    profit_card_bank = fields.CharField(null=True, max_length=255, description='分成打款账号所属银行')
    provider_status = fields.IntField(default=0, description='0未激活 1正常 2禁用')
    car_group_list = fields.ReverseRelation['CarGroup']
    order_list = fields.ReverseRelation['Order']
    withdraw_list = fields.ReverseRelation['ProviderWithdraw']

    class Meta:
        table_description = "场地提供方"
        table = "field_provider"


class ProviderWithdraw(TimestampMixin):
    field_provider = fields.ForeignKeyField('field_provider.FieldProvider', related_name='withdraw_list',
                                            description='场地提供方')
    profit_status = fields.IntField(null=False, default=2,
                                    description='分成状态 0->未申请，2->已申请，3->已批准，4->已打款， 5->已拒绝')
    during_start = fields.DatetimeField(description='结算周期的开始时间')
    during_end = fields.DatetimeField(description="结算周期的结束时间")

    class Meta:
        table_description = "提供方提现记录"
        table = "provider_withdraw"
