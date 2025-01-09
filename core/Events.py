# -*- coding:utf-8 -*-
"""
@Created on : 2022/4/22 22:02
@Author: binkuolo
@Des: fastapi事件监听
"""
import threading
from typing import Callable
from fastapi import FastAPI

from core import AppTask
from database.mysql import register_mysql
from database.redis import sys_cache, code_cache
from redis.asyncio import Redis

from mqtt.mqtt_car import car_sub


def startup(app: FastAPI) -> Callable:
    """
    FastApi 启动完成事件
    :param app: FastAPI
    :return: start_app
    """
    async def app_start() -> None:
        # APP启动完成后触发
        print("fastapi已启动")
        # 注册数据库
        print("注册数据库")
        await register_mysql(app)
        # 注入缓存到app state
        app.state.cache = await sys_cache()
        app.state.code_cache = await code_cache()

        print("启动MQTT")
        # 单独线程启动，防止阻挡主框架运行
        mqtt_thread = threading.Thread(target=car_sub)
        mqtt_thread.daemon = True  # 设置为守护线程
        mqtt_thread.start()

        # 定时任务
        print("启动定时任务")
        AppTask.startAsyncSchedulerTask()
        pass
    return app_start


def stopping(app: FastAPI) -> Callable:
    """
    FastApi 停止事件
    :param app: FastAPI
    :return: stop_app
    """
    async def stop_app() -> None:
        # APP停止时触发
        print("fastapi已停止")
        cache: Redis = await app.state.cache
        code: Redis = await app.state.code_cache
        await cache.close()
        await code.close()

    return stop_app
