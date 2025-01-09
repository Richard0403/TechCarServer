# -*- coding:utf-8 -*-
"""
@Time : 2022/4/24 10:11 AM
@Author: binkuolo
@Des: 常用返回类型封装
"""
from typing import List


def res_antd(data: List = None, total: int = 0, code: bool = True):
    """
    支持ant-design-table 返回的格式
    :param code:
    :param data:
    :param total:
    :return:
    """
    result = {
        "success": code,
        "data": data,
        "total": total
    }
    return result


def base_response(code, msg, data=None):
    """基础返回格式"""
    result = {
        "code": code,
        "message": msg,
        "data": data
    }
    return result


def success(data=None, msg='ok'):
    """成功返回格式"""
    return base_response(0, msg, data)


def fail(code=-1, msg='', data=None):
    """失败返回格式"""
    return base_response(code, msg, data)


ERROR_NO_ACCOUNT = -10001
ERROR_LOGIN_FAILED = -10002
ERROR_PRE_ORDER_FAILED = -10003
