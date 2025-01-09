# -*- coding:utf-8 -*-
"""
@Created on : 2022/4/22 22:02
@Author: binkuolo
@Des: api路由
"""
from fastapi import APIRouter
from api.endpoints.test import test_oath2
from api.endpoints import api_user, api_role, api_access, websocket
from api.extends import api_sms, api_wechat, api_cos, api_we_pay, api_product, api_order, api_tech_car

api_router = APIRouter(prefix="/api/v1")
api_router.post("/test/oath2", tags=["测试oath2授权"])(test_oath2)
api_router.include_router(api_user.router, prefix='/admin', tags=["用户管理"])
api_router.include_router(api_role.router, prefix='/admin', tags=["角色管理"])
api_router.include_router(api_access.router, prefix='/admin', tags=["权限管理"])
api_router.include_router(websocket.router, prefix='/ws', tags=["WebSocket"])
api_router.include_router(api_wechat.router, prefix='/wechat', tags=["微信授权"])
api_router.include_router(api_sms.router, prefix='/sms', tags=["短信接口"])
api_router.include_router(api_cos.router, prefix='/cos', tags=["对象存储接口"])
api_router.include_router(api_we_pay.router, prefix='/wepay', tags=["微信支付"])
api_router.include_router(api_product.router, prefix='/product', tags=["商品相关"])
api_router.include_router(api_order.router, prefix='/order', tags=["订单相关"])
api_router.include_router(api_tech_car.router, prefix='/tech_car', tags=["小车相关"])

