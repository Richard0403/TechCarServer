from core.Auth import check_permissions
from core.Response import success, fail
from sts.sts import Sts
from fastapi import APIRouter, Security, Request

from core.Utils import random_str
from models.product import Product

router = APIRouter()


@router.get('/get/product', summary="获取当前用户信息",)
async def get_product_list(req: Request):
    product_list = await Product.all()
    return success(product_list)
