# -*- coding:utf-8 -*-
"""
@Time : 2022/4/27 5:29 PM
@Author: binkuolo
@Des: schemas模型
"""
from datetime import datetime
from pydantic import Field, BaseModel, validator
from typing import Optional, List
from schemas.base import BaseResp, ResAntTable


class OrderQuery(BaseModel):
    page: int = Field(ge=1, le=100, description="页数")
    page_size: int = Field(ge=1, le=20)
    order_status: Optional[int] = Field(ge=-1, le=8,
                                        description="订单状态，-1->全部， 1->已支付， 2->售后中和退款单")


class ProductInfo(BaseModel):
    id: int
    real_price: int
    origin_price: int
    minute: int
    description: str
    sell_count: int
    status: int
    thumb: str
    buy_limit: int
    update_time: datetime
    create_time: datetime

    class Config:
        orm_mode = True


class OrderInfo(BaseModel):
    id: int
    trade_no: str
    product_num: int
    pay_amount: int
    status: int
    transaction_id: Optional[str]
    openid: str
    product: Optional[ProductInfo]
    update_time: datetime
    create_time: datetime

    class Config:
        orm_mode = True


class OrderList(BaseResp):
    data: List[OrderInfo]


class OrderDetail(BaseResp):
    data: OrderInfo
