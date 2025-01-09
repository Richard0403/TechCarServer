# -*- coding:utf-8 -*-
"""
@Time : 2022/4/24 10:15 AM
@Author: binkuolo
@Des: mysql数据库
"""

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
import os

from config import Config, settings

# -----------------------数据库配置-----------------------------------
DB_ORM_CONFIG = {
    "connections": {
        "base": {
            'engine': 'tortoise.backends.mysql',
            "credentials": {
                'host': os.getenv('BASE_HOST', settings.DATABASE_SERVER),
                'user': os.getenv('BASE_USER', 'xxx'), #配置数据库用户
                'password': os.getenv('BASE_PASSWORD', 'xxxx'), #配置数据库密码
                'port': int(os.getenv('BASE_PORT', 3306)),
                'database': os.getenv('BASE_DB', 'xxxxx'), #配置数据库名字
            }
        },
        # "db2": {
        #     'engine': 'tortoise.backends.mysql',
        #     "credentials": {
        #         'host': os.getenv('DB2_HOST', '127.0.0.1'),
        #         'user': os.getenv('DB2_USER', 'root'),
        #         'password': os.getenv('DB2_PASSWORD', '123456'),
        #         'port': int(os.getenv('DB2_PORT', 3306)),
        #         'database': os.getenv('DB2_DB', 'db2'),
        #     }
        # },
        # "db3": {
        #     'engine': 'tortoise.backends.mysql',
        #     "credentials": {
        #         'host': os.getenv('DB3_HOST', '127.0.0.1'),
        #         'user': os.getenv('DB3_USER', 'root'),
        #         'password': os.getenv('DB3_PASSWORD', '123456'),
        #         'port': int(os.getenv('DB3_PORT', 3306)),
        #         'database': os.getenv('DB3_DB', 'db3'),
        #     }
        # },

    },
    "apps": {

        "base": {"models": ["models.base"], "default_connection": "base"},
        "field_provider": {"models": ["models.field_provider"], "default_connection": "base"},
        "product": {"models": ["models.product"], "default_connection": "base"},
        "tech_car": {"models": ["models.tech_car"], "default_connection": "base"},

        # "db2": {"models": ["models.db2"], "default_connection": "db2"},
        # "db3": {"models": ["models.db3"], "default_connection": "db3"}
    },
    'use_tz': False,
    'timezone': 'Asia/Shanghai'
}


async def register_mysql(app: FastAPI):
    # 注册数据库
    register_tortoise(
        app,
        config=DB_ORM_CONFIG,
        generate_schemas=True,
        add_exception_handlers=False,
    )
