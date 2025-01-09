# -*- coding:utf-8 -*-
"""
@Time : 2022/6/4 2:54 PM
@Author: binkuolo
@Des: 微信授权
"""
import os
import uuid

import requests
from fastapi import Request, APIRouter
from redis.asyncio import Redis

from config import settings
from core import OssTool, ImageUtil
from core.Auth import create_access_token
from core.Response import fail, success, ERROR_NO_ACCOUNT
from models.base import User, UserWechat
from schemas import user, base
from wxmini.WxMiniConfig import wxMiniSettings

router = APIRouter()


@router.post("/auth/login", summary="用户登录")
async def login_with_code(req: Request, post: user.WxMimiLoginCode):
    # 获取登录信息
    login_json = requests.request('GET',
                                  wxMiniSettings.WX_MINI_LOGIN.format(
                                      wxMiniSettings.WX_MINI_APPID,
                                      wxMiniSettings.WX_MINI_APPID_SECRET,
                                      post.login_code
                                  )).json()
    print("登录信息" + str(login_json))
    openid = login_json['openid']
    unionid = login_json['unionid']
    user = await User.get_or_none(wechat__openid=openid)
    if user:
        jwt_data = {
            "user_id": user.pk,
            "user_type": user.user_type
        }
        jwt_token = create_access_token(data=jwt_data)
        data = {
            "token": jwt_token,
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }
        return success(msg="登录成功", data=data)
    else:
        return fail(code=ERROR_NO_ACCOUNT, msg="无此账号，请用手机code登录")
    pass


@router.post("/auth/register", summary="用户登录注册")
async def register_with_code(req: Request, post: user.WxMiniPhoneNumberCode):
    wx_mini_access_token = await get_access_token(req)
    # 获取登录信息
    login_json = requests.request('GET',
                                  wxMiniSettings.WX_MINI_LOGIN.format(
                                      wxMiniSettings.WX_MINI_APPID,
                                      wxMiniSettings.WX_MINI_APPID_SECRET,
                                      post.login_code
                                  )).json()
    print("登录信息" + str(login_json))

    get_phone_param = {'code': post.phone_num_code}
    get_phone_response = requests.request('POST', wxMiniSettings.WX_MINI_GET_PHONE_URL.format(wx_mini_access_token),
                                          json=get_phone_param)
    phone_json = get_phone_response.json()
    print("获取手机号" + str(phone_json))
    if phone_json['errcode'] == 0:
        phoneNumber = phone_json['phone_info']['purePhoneNumber']
        user = await User.get_or_none(user_phone=phoneNumber)
        if not user:
            # 创建用户
            user = await User.create(
                user_type=False,
                nickname=str(uuid.uuid4()),
                user_phone=phoneNumber,
                user_status=1,
                username=str(uuid.uuid4()),
            )
            if not user:
                return fail(msg=f"用户{post.login_code}创建失败!")
            # 有分配角色
            create_wx_user = await UserWechat.update_or_create(
                user=user,
                openid=login_json['openid'],
                unionid=login_json['unionid'],
                user_phone=phoneNumber)
            if not create_wx_user:
                return fail(msg=f"微信用户{post.login_code}创建失败!")

        jwt_data = {
            "user_id": user.pk,
            "user_type": user.user_type
        }
        jwt_token = create_access_token(data=jwt_data)
        data = {
            "token": jwt_token,
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }
        return success(msg="登录成功", data=data)
    else:
        return fail(msg="获取用户信息失败")


async def get_access_token(req: Request) -> str:
    redis: Redis = await req.app.state.code_cache
    wx_mini_access_token = await redis.get(name="wx_mini_access_token")
    if not wx_mini_access_token:
        token_response = requests.request('GET', wxMiniSettings.WX_MINI_TOKEN_URL)
        result = token_response.json()
        print("获取accessToken" + str(result))
        wx_mini_access_token = result['access_token']
        await redis.set("wx_mini_access_token", wx_mini_access_token, 7200)
    return wx_mini_access_token


@router.post("/auth/get_unlimited_qrcode", summary="获取通用小程序码")
async def get_unlimited_qrcode(req: Request, post: base.WxMiniQrCode):
    wx_mini_access_token = await get_access_token(req)
    qr_json = {
        'page': post.page,
        'scene': post.scene,
        'check_path': False,
        'env_version': post.env_version
    }
    get_qrcode_response = requests.request('POST', wxMiniSettings.WX_MINI_GEN_PATH_CODE.format(wx_mini_access_token),
                                           json=qr_json)

    if get_qrcode_response.status_code == 200:
        file_name = 'qr_code/' + str(uuid.uuid4()) + '.png'
        OssTool.upload_stream(get_qrcode_response.content, file_name)
        file_url = settings.OSS_END_POINT + file_name
        print('二维码已生成，保存为:' + file_url)
        response = {
            'file_url': file_url
        }
        return success(response)
    else:
        print('生成二维码失败:', get_qrcode_response.json())
        return fail(msg='生成二维码失败', data=get_qrcode_response.json())


@router.post("/auth/car_device_qrcode", summary="获取小车的小程序码")
async def get_unlimited_qrcode(req: Request, post: base.WxCarDeviceQrCode):
    wx_mini_access_token = await get_access_token(req)
    qr_json = {
        'page': 'pages/home/home',
        'scene': f'device_id={post.device_id}',
        'check_path': False
    }
    get_qrcode_response = requests.request('POST', wxMiniSettings.WX_MINI_GEN_PATH_CODE.format(wx_mini_access_token),
                                           json=qr_json)

    if get_qrcode_response.status_code == 200:
        if not os.path.exists('qr_code'):
            os.mkdir('qr_code')
        file_name = f'qr_code/{post.device_id}_{str(uuid.uuid4())}.png'

        with open(file_name, 'wb') as f:
            f.write(get_qrcode_response.content)
        convert_file = ImageUtil.add_device_id_to_qrcode(file_name, post.device_id, del_origin_after_handle=True)

        OssTool.upload_file(convert_file, file_name)
        file_url = settings.OSS_END_POINT + file_name
        print('二维码已生成，保存为:' + file_url)
        response = {
            'file_url': file_url
        }
        return success(response)
    else:
        print('生成二维码失败:', get_qrcode_response.json())
        return fail(msg='生成二维码失败', data=get_qrcode_response.json())
