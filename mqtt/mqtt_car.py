# sub.py
# python 3.6+

import asyncio
import json
import logging
import uuid

from paho.mqtt import client as mqtt_client

from core import Logger
from core.Logger import mqtt_logger
from mqtt.save_mqtt_msg import save_location, finish_use_car, start_use_car, manual_close_car, refresh_car_battery

# mqtt_server = "mqtt://49.232.209.33:1883"
broker = '49.232.209.33'
port = 1883
user_name = "server_develop"
user_pwd = "two13145@"
topic_server_to_client = "server_to_client/"
topic_client_to_server = "client_to_server/+"
server_client_id = "home_90893lkii-29038908-koehf-32132_develop"

car_mqtt_client: mqtt_client = None
app_event_loop = asyncio.get_event_loop()


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            mqtt_logger.info("Connected to MQTT Broker!")
            # publish(client, "863644071795703", "config,get,lbsloc\r\n")
            # publish(client, "863644071795703", "config,get,gps\r\n")
            # publish(client, "863644071795703", "config,set,doout,1,1\r\n")
            # publish(client, "863644071795703", "config,get,aiv,1\r\n")
            # start_car('863644071795703', 1)
        else:
            mqtt_logger.error("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id=server_client_id)
    client.username_pw_set(user_name, user_pwd)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    index = 1
    def on_message(client, userdata, msg):
        mqtt_logger.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        imei = str(msg.topic).split("/")[-1]
        msg_payload = str(msg.payload.decode())
        if msg_payload.startswith('lbs_') or msg_payload.startswith('gps_'):
            # 自动定位信息
            mqtt_logger.info(f"获取到基站定位信息：{imei}==={msg_payload}")
            asyncio.run_coroutine_threadsafe(
                save_location(imei,
                              float(msg_payload.split('_')[1]),
                              float(msg_payload.split('_')[2]),
                              msg_payload.startswith('gps_')),
                app_event_loop
            )
        elif msg_payload.startswith('start_close_task_start'):
            # 开始打开车辆电源
            mqtt_logger.info(f"打开车辆电源：{imei}==={msg_payload}")
            asyncio.run_coroutine_threadsafe(start_use_car(imei), app_event_loop)
        elif msg_payload.startswith('start_close_task_finish'):
            # 游戏结束关闭电源
            mqtt_logger.info(f"游戏结束关闭电源：{imei}==={msg_payload}")
            # 刷新一下电池电量
            get_car_battery(imei)
            asyncio.run_coroutine_threadsafe(finish_use_car(imei), app_event_loop)
        elif msg_payload.find('config,lbsloc,ok') != -1:
            # 手动基站定位
            mqtt_logger.info(f"手动获取基站定位：{imei}==={msg_payload}")
            msg_payload = msg_payload.replace('\r\n', '')
            asyncio.run_coroutine_threadsafe(
                save_location(imei,
                              float(msg_payload.split(',')[-1]),
                              float(msg_payload.split(',')[-2]),
                              False),
                app_event_loop)
        elif msg_payload.find('config,gps,ok') != -1:
            # 手动gps定位
            mqtt_logger.info(f"手动获取GPS定位：{imei}==={msg_payload}")
            msg_payload = msg_payload.replace('\r\n', '')
            asyncio.run_coroutine_threadsafe(
                save_location(imei,
                              float(msg_payload.split(',')[-1]),
                              float(msg_payload.split(',')[-3]),
                              True),
                app_event_loop)
        elif msg_payload.find('config,doout,ok') != -1:
            # 手动关闭命令
            mqtt_logger.info(f"手动关闭命令：{imei}==={msg_payload}")
            asyncio.run_coroutine_threadsafe(manual_close_car(imei), app_event_loop)
        elif msg_payload.find('config,aiv,ok') != -1:
            # 电池电压检测
            mqtt_logger.info(f"获取电池电压：{imei}==={msg_payload}")
            battery = int(msg_payload.split(',')[-1])
            asyncio.run_coroutine_threadsafe(refresh_car_battery(imei, battery), app_event_loop)
        else:
            mqtt_logger.info(f"未知命令不做处理：{imei}==={msg_payload}")

    client.subscribe(topic_client_to_server, qos=2)
    client.on_message = on_message


def publish(client: mqtt_client, imei, msg):
    topic = topic_server_to_client + imei
    result = client.publish(topic, msg, qos=2)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        mqtt_logger.info(f"Send `{msg}` to topic `{topic}`")
    else:
        mqtt_logger.error(f"Failed to send message to topic {topic}")


def car_sub():
    global car_mqtt_client
    car_mqtt_client = connect_mqtt()
    subscribe(car_mqtt_client)
    car_mqtt_client.loop_forever()


def start_car(device_id: str, minute):
    cmd = {
        'cmd': 'onoff1',
        'during': minute * 60 * 1000
    }
    mqtt_logger.info(f"发送启动车辆命令:{json.dumps(cmd)}")
    publish(car_mqtt_client, device_id, json.dumps(cmd))
    pass


def get_car_location(device_id: str):
    cmd_lbs = 'config,get,lbsloc\r\n'
    cmd_gps = 'config,get,gps\r\n'
    mqtt_logger.info(f"发送获取定位信息命令：{cmd_lbs}----{cmd_gps}")
    publish(car_mqtt_client, device_id, cmd_lbs)
    publish(car_mqtt_client, device_id, cmd_gps)
    pass


def get_car_battery(device_id: str):
    cmd_battery = 'config,get,aiv,1\r\n'
    mqtt_logger.info(f"发送获取电压命令：{cmd_battery}")
    publish(car_mqtt_client, device_id, cmd_battery)
    pass


if __name__ == '__main__':
    car_sub()
