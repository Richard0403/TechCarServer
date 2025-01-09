# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
from random import sample
from string import ascii_letters, digits
import time
import uuid

from tortoise.functions import Sum
from wechatpayv3 import WeChatPay, WeChatPayType
from fastapi import Request, APIRouter, Security, HTTPException

from core import Logger
from core.Auth import check_permissions
from core.Response import success, fail, ERROR_PRE_ORDER_FAILED
from models.base import User
from models.tech_car import CarInfo, CarUseRecord
from models.product import Product, Order, AccountRecord
from mqtt import mqtt_car
from schemas.wepay import WePayPreOrder, MockPayNotify
from wxmini.WxMiniConfig import wxMiniSettings

# 微信支付商户号（直连模式）或服务商商户号（服务商模式，即sp_mchid)

# 商户证书私钥
with open(wxMiniSettings.WXPAY_CLIENT_PRIKEY) as f:
    PRIVATE_KEY = f.read()

# 接入模式:False=直连商户模式，True=服务商模式
PARTNER_MODE = False

# 代理设置，None或者{"https": "http://10.10.1.10:1080"}，详细格式参见https://requests.readthedocs.io/en/latest/user/advanced/#proxies
PROXY = None

# 请求超时时间配置
TIMEOUT = (10, 30)  # 建立连接最大超时时间是10s，读取响应的最大超时时间是30s

# 初始化
wxpay = WeChatPay(
    wechatpay_type=WeChatPayType.NATIVE,
    mchid=wxMiniSettings.WXPAY_MCHID,
    private_key=PRIVATE_KEY,
    cert_serial_no=wxMiniSettings.WXPAY_SERIALNO,
    apiv3_key=wxMiniSettings.WXPAY_APIV3_KEY,
    appid=wxMiniSettings.WX_MINI_APPID,
    notify_url=wxMiniSettings.NOTIFY_URL,
    cert_dir=wxMiniSettings.CERT_DIR,
    logger=Logger.wepay_logger,
    partner_mode=PARTNER_MODE,
    proxy=PROXY,
    timeout=TIMEOUT
)

router = APIRouter()


@router.route('/pay')
def pay():
    # 以native下单为例，下单成功后即可获取到'code_url'，将'code_url'转换为二维码，并用微信扫码即可进行支付测试。
    out_trade_no = ''.join(sample(ascii_letters + digits, 8))
    description = 'demo-description'
    amount = 1
    code, message = wxpay.pay(
        description=description,
        out_trade_no=out_trade_no,
        amount={'total': amount},
        pay_type=WeChatPayType.NATIVE
    )
    # return jsonify({'code': code, 'message': message})
    return success(msg=message)


@router.route('/pay_jsapi')
def pay_jsapi():
    # 以jsapi下单为例，下单成功后，将prepay_id和其他必须的参数组合传递给JSSDK的wx.chooseWXPay接口唤起支付
    out_trade_no = ''.join(sample(ascii_letters + digits, 8))
    description = 'demo-description'
    amount = 1
    payer = {'openid': 'demo-openid'}
    code, message = wxpay.pay(
        description=description,
        out_trade_no=out_trade_no,
        amount={'total': amount},
        pay_type=WeChatPayType.JSAPI,
        payer=payer
    )
    result = json.loads(message)
    if code in range(200, 300):
        prepay_id = result.get('prepay_id')
        timestamp = str(int(time.time()))
        noncestr = str(uuid.uuid4()).replace('-', '')
        package = 'prepay_id=' + prepay_id
        sign = wxpay.sign([wxMiniSettings.WX_MINI_APPID, timestamp, noncestr, package])
        signtype = 'RSA'
        return success(data={
            'appId': wxMiniSettings.WX_MINI_APPID,
            'timeStamp': timestamp,
            'nonceStr': noncestr,
            'package': 'prepay_id=%s' % prepay_id,
            'signType': signtype,
            'paySign': sign
        })
    else:
        return fail(code=ERROR_PRE_ORDER_FAILED, msg="支付预订单生成失败")


@router.post('/pay_h5')
def pay_h5():
    # 以h5下单为例，下单成功后，将获取的的h5_url传递给前端跳转唤起支付。
    out_trade_no = 'order_'.join(sample(ascii_letters + digits, 8)).join(str(time.time_ns()))
    description = 'demo-description'
    amount = 1
    scene_info = {'payer_client_ip': '1.2.3.4', 'h5_info': {'type': 'Wap'}}
    code, message = wxpay.pay(
        description=description,
        out_trade_no=out_trade_no,
        amount={'total': amount},
        pay_type=WeChatPayType.H5,
        scene_info=scene_info
    )
    return success({'message': message})


@router.post('/pay_mini_program', dependencies=[Security(check_permissions)], summary="微信预支付")
async def pay_mini_program(req: Request, post: WePayPreOrder):
    product = await Product.get_or_none(id=post.product_id)
    if not product:
        return fail(msg="产品获取失败，请换个产品下单")
    user_id = req.state.user_id
    # user = await User.get_or_none(id=user_id)
    user = await User.filter(id=user_id).prefetch_related('wechat').first()
    openid = user.wechat.openid

    total_score = await Order.filter(user_id=user_id, product__id=post.product_id, status=1).annotate(
        total=Sum('product_num')).first()
    bought_count = 0
    if total_score:
        bought_count = total_score.total
    if bought_count + post.product_num > product.buy_limit:
        return fail(msg=f'该产品仅限购买{product.buy_limit}个')

    car_info = await CarInfo.filter(device_id=post.device_id).prefetch_related('group__field_provider').first()
    if not car_info:
        return fail(msg='该设备不存在，请换个小车扫描二维码')
    if car_info.status == 1:
        return fail(msg='车辆正在被别人使用，请换个设备扫码')
    if car_info.battery_electric < 25:
        return fail(msg='车辆电量不足，请换辆车扫码，或联系客服更换电池')
    # 创建订单记录
    out_trade_no = 'order_' + str(time.time_ns()) + ''.join(sample(ascii_letters + digits, 5))
    amount = product.real_price * post.product_num
    order = await Order.create(trade_no=out_trade_no,
                               product_num=post.product_num,
                               pay_amount=amount,
                               openid=openid,
                               product=product,
                               user=user,
                               car_info=car_info,
                               field_provider=car_info.group.field_provider,
                               profit_percent=car_info.group.field_provider.profit_percent,
                               profit_amount=int(amount * car_info.group.field_provider.profit_percent / 100),
                               profit_status=0)
    if not order:
        return fail(msg="创建订单失败")

    # 以小程序下单为例，下单成功后，将prepay_id和其他必须的参数组合传递给小程序的wx.requestPayment接口唤起支付

    description = product.description + 'x' + str(post.product_num)

    payer = {'openid': openid}

    code, message = wxpay.pay(
        description=description,
        out_trade_no=out_trade_no,
        amount={'total': amount},
        pay_type=WeChatPayType.MINIPROG,
        payer=payer
    )

    result = json.loads(message)
    if code in range(200, 300):
        prepay_id = result.get('prepay_id')
        timestamp = str(int(time.time()))
        noncestr = str(uuid.uuid4()).replace('-', '')
        package = 'prepay_id=' + prepay_id
        sign = wxpay.sign(data=[wxMiniSettings.WX_MINI_APPID, timestamp, noncestr, package])
        signtype = 'RSA'
        return success({
            'appId': wxMiniSettings.WX_MINI_APPID,
            'timeStamp': timestamp,
            'nonceStr': noncestr,
            'package': 'prepay_id=%s' % prepay_id,
            'signType': signtype,
            'paySign': sign,
            'tradeNo': out_trade_no
        })
    else:
        return fail({'reason': result.get('code')})


@router.route('/pay_app')
def pay_app():
    # 以app下单为例，下单成功后，将prepay_id和其他必须的参数组合传递给IOS或ANDROID SDK接口唤起支付
    out_trade_no = ''.join(sample(ascii_letters + digits, 8))
    description = 'demo-description'
    amount = 1
    code, message = wxpay.pay(
        description=description,
        out_trade_no=out_trade_no,
        amount={'total': amount},
        pay_type=WeChatPayType.APP
    )
    result = json.loads(message)
    if code in range(200, 300):
        prepay_id = result.get('prepay_id')
        timestamp = str(int(time.time()))
        noncestr = str(uuid.uuid4()).replace('-', '')
        package = 'Sign=WXPay'
        sign = wxpay.sign(data=[wxMiniSettings.WX_MINI_APPID, timestamp, noncestr, prepay_id])
        return success({
            'appid': wxMiniSettings.WX_MINI_APPID,
            'partnerid': wxMiniSettings.WXPAY_MCHID,
            'prepayid': prepay_id,
            'package': package,
            'nonceStr': noncestr,
            'timestamp': timestamp,
            'sign': sign
        })
    else:
        return fail({'reason': result.get('code')})


@router.route('/pay_codepay')
def pay_codepay():
    # 以付款码支付为例，终端条码枪扫描用户付款码将解码后的auth_code放入payer传递给微信支付服务器扣款。
    out_trade_no = ''.join(sample(ascii_letters + digits, 8))
    description = 'demo-description'
    amount = 1
    payer = {'auth_code': '130061098828009406'}
    scene_info = {'store_info': {'id': '0001'}}
    code, message = wxpay.pay(
        description=description,
        out_trade_no=out_trade_no,
        amount={'total': amount},
        payer=payer,
        scene_info=scene_info,
        pay_type=WeChatPayType.CODEPAY
    )
    result = json.loads(message)
    if code in range(200, 300):
        trade_state = result.get('trade_state')
        trade_state_desc = result.get('trade_state_desc')
        if trade_state == 'SUCCESS':
            # 扣款成功，提示终端做后续处理
            return success({'reason': trade_state_desc})
        else:
            # 扣款失败，提示终端做后续处理
            return fail({'reason': trade_state_desc})
    else:
        return fail({'reason': result.get('code')})


@router.post('/notify', summary="支付回调通知")
async def notify(request: Request):
    body = await request.body()
    result = wxpay.callback(request.headers, body)
    Logger.wepay_logger.info("微信支付回调结果")
    Logger.wepay_logger.info(result)
    if result and result.get('event_type') == 'TRANSACTION.SUCCESS':
        Logger.wepay_logger.info("微信支付回调解析成功")
        resp = result.get('resource')
        appid = resp.get('appid')
        mchid = resp.get('mchid')
        out_trade_no = resp.get('out_trade_no')
        transaction_id = resp.get('transaction_id')
        trade_type = resp.get('trade_type')
        trade_state = resp.get('trade_state')
        trade_state_desc = resp.get('trade_state_desc')
        bank_type = resp.get('bank_type')
        attach = resp.get('attach')
        success_time = resp.get('success_time')
        payer = resp.get('payer').get('openid')
        amount = resp.get('amount').get('total')

        # 根据返回参数进行必要的业务处理，处理完后返回200或204
        await Order.filter(trade_no=out_trade_no).update(status=1,
                                                         profit_status=1,
                                                         transaction_id=transaction_id)
        Logger.wepay_logger.info(f"更新订单状态：{out_trade_no}")
        related_order = await (Order.filter(trade_no=out_trade_no)
                               .prefetch_related('product', 'user', 'car_info')
                               .first())
        # 变动时间数量
        add_amount = related_order.product.minute * related_order.product_num
        latest_record = await (AccountRecord.filter(user__id=related_order.user.id)
                               .order_by('-update_time').first())

        target_amount = (latest_record.rest_minute + add_amount) if latest_record else add_amount
        await AccountRecord.create(rest_minute=target_amount,
                                   change_minute=add_amount,
                                   source=2,
                                   user=related_order.user)
        Logger.wepay_logger.info(f"更新用户时间变动记录：{out_trade_no}")
        # 更新用户信息
        await User.filter(id=related_order.user.id).update(rest_minute=target_amount)
        Logger.wepay_logger.info(f"更新用户时间信息：{out_trade_no}")
        # 增加车辆使用记录
        car_record = await CarUseRecord.create(status=0,
                                               begin_time=datetime.datetime.now(),
                                               car_info=related_order.car_info,
                                               user_info=related_order.user,
                                               order_info=related_order,
                                               minute=related_order.product.minute)
        Logger.wepay_logger.info(f"增加车辆使用记录：{out_trade_no}")
        # 启动车辆
        mqtt_car.start_car(related_order.car_info.device_id, car_record.minute)
        Logger.wepay_logger.info(f"发送启动车辆命令：{out_trade_no}")
        return {'code': 'SUCCESS', 'message': '成功'}
    else:
        Logger.wepay_logger.error("支付回调解析错误")
        raise HTTPException(500, "支付回调解析错误")


@router.post('/mock_notify', summary="支付回调通知MOCK测试")
async def mock_notify(request: Request, post: MockPayNotify):

    await Order.filter(trade_no=post.out_trade_no).update(status=1,
                                                          transaction_id=post.transaction_id,
                                                          profit_status=1)
    related_order = await (Order.filter(trade_no=post.out_trade_no)
                           .prefetch_related('product', 'user', 'car_info')
                           .first())
    # 变动时间数量
    add_amount = related_order.product.minute * related_order.product_num
    latest_record = await (AccountRecord.filter(user__id=related_order.user.id)
                           .order_by('-update_time').first())
    target_amount = (latest_record.rest_minute + add_amount) if latest_record else add_amount
    await AccountRecord.create(rest_minute=target_amount,
                               change_minute=add_amount,
                               source=2,
                               user=related_order.user)
    # 更新用户信息
    await User.filter(id=related_order.user.id).update(rest_minute=target_amount)

    # 增加车辆使用记录
    car_record = await CarUseRecord.create(status=0,
                                           car_info=related_order.car_info,
                                           user_info=related_order.user,
                                           order_info=related_order,
                                           minute=related_order.product.minute)
    # 启动车辆
    mqtt_car.start_car(related_order.car_info.device_id, car_record.minute)
    return {'code': 'SUCCESS', 'message': '成功'}
