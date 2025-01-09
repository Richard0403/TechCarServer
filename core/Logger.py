# -*- coding: utf-8 -*-

import logging
import os
from logging.handlers import RotatingFileHandler

# 日志文件大小限制 500MB
LOG_FILE_MAX_SIZE = 500 * 1024 * 1024  # 500MB
BACKUP_COUNT = 8  # 最多保留8个文件

# 日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)
LOG_DIR = 'log_dir'

# 创建RotatingFileHandler，限制日志大小并保留8个文件
def create_rotating_handler(log_file):
    handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_FILE_MAX_SIZE,
        backupCount=BACKUP_COUNT
    )
    handler.setFormatter(formatter)
    return handler


# 创建StreamHandler输出到控制台
def create_console_handler():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    return console_handler


if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)
# 创建 api_logger
api_logger = logging.getLogger("api_logger")
api_logger.setLevel(logging.DEBUG)  # 设定日志级别
api_logger.addHandler(create_rotating_handler(f"{LOG_DIR}/api_logger.log"))
api_logger.addHandler(create_console_handler())

# 创建 db_logger
db_logger = logging.getLogger("db_logger")
db_logger.setLevel(logging.DEBUG)  # 设定日志级别
db_logger.addHandler(create_rotating_handler(f"{LOG_DIR}/db_logger.log"))
db_logger.addHandler(create_console_handler())

# 创建 mqtt_logger
mqtt_logger = logging.getLogger("mqtt_logger")
mqtt_logger.setLevel(logging.DEBUG)  # 设定日志级别
mqtt_logger.addHandler(create_rotating_handler(f"{LOG_DIR}/mqtt_logger.log"))
mqtt_logger.addHandler(create_console_handler())

# 创建 wepay_logger
wepay_logger = logging.getLogger("wepay_logger")
wepay_logger.setLevel(logging.DEBUG)  # 设定日志级别
wepay_logger.addHandler(create_rotating_handler(f"{LOG_DIR}/wepay_logger.log"))
wepay_logger.addHandler(create_console_handler())

# 创建 wepay_logger
task_logger = logging.getLogger("task_logger")
task_logger.setLevel(logging.DEBUG)  # 设定日志级别
task_logger.addHandler(create_rotating_handler(f"{LOG_DIR}/task_logger.log"))
task_logger.addHandler(create_console_handler())

if __name__ == '__main__':
    api_logger.info("API request received")
    db_logger.debug("Database query executed")
    mqtt_logger.error("mqtt error")
