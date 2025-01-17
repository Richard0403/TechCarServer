# -*- coding:utf-8 -*-
"""
@Time : 2022/5/4 10:54 PM
@Author: binkuolo
@Des: 基础schemas
"""
from pydantic import BaseModel, Field
from typing import List, Any, Optional


class BaseResp(BaseModel):
    code: int = Field(description="状态码")
    message: str = Field(description="信息")
    data: Optional[List] = Field(description="数据")


class ResAntTable(BaseModel):
    success: bool = Field(description="状态码")
    data: List = Field(description="数据")
    total: int = Field(description="总条数")


class WebsocketMessage(BaseModel):
    action: Optional[str]
    user: Optional[int]
    data: Optional[Any]


class WechatOAuthData(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    unionid: Optional[str]
    scope: str
    openid: str


class WechatUserInfo(BaseModel):
    openid: str
    nickname: str
    sex: int
    city: str
    province: str
    country: str
    headimgurl: str
    unionid: Optional[str]


class WxMiniQrCode(BaseModel):
    page: str
    scene: str
    env_version: str


class WxCarDeviceQrCode(BaseModel):
    device_id: str


class PageQuery(BaseModel):
    page: int = Field(ge=1, le=100, description="页数")
    page_size: int = Field(ge=1, le=20)


class TradeNoQuery(BaseModel):
    trade_no: str


class GroupCarsQuery(BaseModel):
    group_id: int

