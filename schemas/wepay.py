from pydantic import BaseModel, Field
from typing import List, Optional
from schemas.base import ResAntTable
from datetime import datetime


class WePayPreOrder(BaseModel):
    product_id: int = Field(description="产品id")
    product_num: int = Field(description="产品数量")
    device_id: str = Field(description='设备ID')


class MockPayNotify(BaseModel):
    out_trade_no: str = Field(description="后台交易订单号")
    transaction_id: str = Field(description="微信支付订单号")
