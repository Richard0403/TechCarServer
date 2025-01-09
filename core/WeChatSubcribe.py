
import requests
from redis.asyncio.client import Redis

from api.extends.api_wechat import get_access_token
from core import Events
from core.Logger import mqtt_logger
from wxmini.WxMiniConfig import wxMiniSettings

code_cache_redis = None
async def get_wx_access_token() -> str:
    global code_cache_redis
    if not code_cache_redis:
        code_cache_redis = await Events.code_cache()

    wx_mini_access_token = await code_cache_redis.get(name="wx_mini_access_token")
    if not wx_mini_access_token:
        token_response = requests.request('GET', wxMiniSettings.WX_MINI_TOKEN_URL)
        result = token_response.json()
        print("获取accessToken" + str(result))
        wx_mini_access_token = result['access_token']
        await code_cache_redis.set("wx_mini_access_token", wx_mini_access_token, 7200)
    return wx_mini_access_token


async def sendMinuteRestMsg(user_open_id: str, device_id: str, minute: int):
    pass
    wx_mini_access_token = await get_wx_access_token()
    tips = f"您的小车仅剩余{minute}分钟，请尽快还车" if minute > 0 else f'时间已用完，请继续扫码使用，或尽快还车'
    msg_body = {
      "touser": user_open_id,
      "template_id": wxMiniSettings.SubscribeTemplate.get('rest_minute'),
      "page": "home/home?device_id=" + device_id,
      "data": {
          "amount1": {
              "value": str(minute)
          },
          "thing2": {
              "value": tips
          }
      }
    }
    send_msg_response = requests.request('POST', wxMiniSettings.WX_MINI_SEND_SUBSCRIBE_MSG.format(wx_mini_access_token),
                                           json=msg_body).json()
    if send_msg_response['errcode'] == 0:
        mqtt_logger.info(f"发送剩余分钟数消息成功，用户：{user_open_id}，剩余分钟数：{minute}")
    else:
        mqtt_logger.error(f"发送剩余分钟数消息失败，用户：{user_open_id}，剩余分钟数：{minute}, errcode:{send_msg_response.errcode}")
