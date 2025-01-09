from fastapi import APIRouter, Security, Request, Depends

from core.Auth import check_permissions
from core.Response import success
from models.product import Order
from schemas.order import OrderQuery, OrderList

router = APIRouter()


@router.get('/get/user_order', summary="获取当前用户的订单列表",
            response_model=OrderList,
            dependencies=[Security(check_permissions)])
async def get_user_order(req: Request, query: OrderQuery = Depends()):
    user_id = req.state.user_id

    offset = (query.page - 1) * query.page_size
    filters = {}
    if query.order_status in (1, 2):
        filters['status'] = query.order_status

    order_list = await (Order.filter(user__id=user_id, **filters)
                        .prefetch_related('product')
                        .order_by("-create_time")
                        .offset(offset)
                        .limit(query.page_size))
    # 获取当前页的数据列表
    return success(order_list)
