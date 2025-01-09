
# -*- coding:utf-8 -*-
"""
@Created on : 2022/4/22 22:02
@Author: binkuolo
@Des: 基本配置文件
"""


from pydantic import BaseSettings


class WxMiniConfig(BaseSettings):
    WX_MINI_APPID = "xxxx"
    WX_MINI_APPID_SECRET = "xxxx"

    WX_MINI_TOKEN_URL = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                         .format(WX_MINI_APPID, WX_MINI_APPID_SECRET))
    WX_MINI_GET_PHONE_URL = "https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={}"
    WX_MINI_LOGIN = ("https://api.weixin.qq.com/sns/jscode2session?grant_type=authorization_code&appid={}"
                     "&secret={}&js_code={}")
    # 获取无限小程序码
    WX_MINI_GEN_PATH_CODE = 'https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={}'
    # 微信小程序发送订阅消息
    WX_MINI_SEND_SUBSCRIBE_MSG = 'https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={}'

    WXPAY_MCHID = "xxxxx"
    # API v3秘钥
    WXPAY_APIV3_KEY = "xxxxx"
    # 微信支付结果回调接口
    WXPAY_NOTIFYURL = "微信支付结果回调接口"
    # 商户证书序列号
    WXPAY_SERIALNO = "xxxxxxx"
    # 商户私钥
    WXPAY_CLIENT_PRIKEY = "wxmini/wepay_cert/apiclient_key.pem"
    # 商品描述(统一下单接口用到)
    WXPAY_PAY_DESC = "商品描述(统一下单接口用到)"
    # 回调地址，也可以在调用接口的时候覆盖, 替换成自己的域名
    NOTIFY_URL = 'https://xx.xx.com/api/v1/wepay/notify'
    # 微信支付平台证书缓存目录，减少证书下载调用次数，首次使用确保此目录为空目录.
    # 初始调试时可不设置，调试通过后再设置，示例值:'./cert'
    CERT_DIR = './cert'

    SubscribeTemplate = {
        # 剩余时间消息通知的模板
        "rest_minute": "xxxxx-xxxxxx"
    }
    pass


wxMiniSettings = WxMiniConfig()
