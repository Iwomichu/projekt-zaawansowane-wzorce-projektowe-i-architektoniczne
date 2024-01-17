from dataclasses import asdict
from decimal import Decimal
from enum import Enum
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from zwpa.model import TransportStatus
from zwpa.workflows.product.HandleProductDetailsWorkflow import (
    HandleProductDetailsWorkflow,
)
from zwpa.workflows.product.ListProductsWorkflow import ListProductsWorkflow
from zwpa.workflows.retail.GetPersonalizedRetailProductViewsWorkflow import (
    GetPersonalizedRetailProductViewsWorkflow,
)
from zwpa.workflows.retail.HandleCheckoutWorkflow import HandleCheckoutWorkflow
from zwpa.workflows.retail.ModifyCartWorkflow import ModifyCartWorkflow
from zwpa.workflows.retail.OrderView import OrderStatus, OrderView
from zwpa.workflows.retail.RetailProductView import (
    PersonalizedRetailProductView,
)
from zwpa.workflows.retail.RetailStatusProductView import RetailStatusProductView
from zwpa.workflows.retail.RetailTransportView import RetailTransportView

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker
from .shared import (
    get_current_user_id,
    session_maker,
    templates,
    rest_cart_manager,
    simple_retail_price_calculator,
)


router = APIRouter(
    prefix="/retail",
    tags=["retail"],
)
user_role_checker = UserRoleChecker(session_maker)
list_products_workflow = ListProductsWorkflow(session_maker)
handle_product_details_workflow = HandleProductDetailsWorkflow(session_maker)
get_personalized_retail_product_views_workflow = (
    GetPersonalizedRetailProductViewsWorkflow(session_maker, rest_cart_manager)
)
modify_car_workflow = ModifyCartWorkflow(session_maker, rest_cart_manager)
handle_checkout_workflow = HandleCheckoutWorkflow(
    session_maker,
    cart_manager=rest_cart_manager,
    retail_transport_price_calculator=simple_retail_price_calculator,
)


class RetailSection(str, Enum):
    LIST = "LIST"
    CART = "CART"


@router.get("/")
def get_product_list(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    query: str = "",
):
    products = get_personalized_retail_product_views_workflow.get_personalized_retail_product_views(
        user_id, query=query
    )
    return templates.TemplateResponse(
        "retail/listProducts.html",
        {
            "request": request,
            "products": [asdict(product) for product in products],
        },
    )


@router.get("/cart/{product_id}/add")
def get_add_item_into_cart(
    user_id: Annotated[int, Depends(get_current_user_id)],
    product_id: int,
    previous_section: RetailSection = RetailSection.LIST,
):
    modify_car_workflow.put_into_cart(user_id, product_id)
    target_section = "/retail"
    if previous_section is RetailSection.CART:
        target_section += "/cart"
    return RedirectResponse(url=target_section, status_code=303)


@router.get("/cart/{product_id}/remove")
def get_remove_item_from_cart(
    user_id: Annotated[int, Depends(get_current_user_id)],
    product_id: int,
    previous_section: RetailSection = RetailSection.LIST,
):
    modify_car_workflow.take_from_cart(user_id, product_id)
    target_section = "/retail"
    if previous_section is RetailSection.CART:
        target_section += "/cart"
    return RedirectResponse(url=target_section, status_code=303)


@router.get("/cart")
def get_cart(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    products = get_personalized_retail_product_views_workflow.get_personalized_retail_product_views(
        user_id, only_already_in_cart=True
    )
    return templates.TemplateResponse(
        "retail/cartView.html",
        {
            "request": request,
            "products": [asdict(product) for product in products],
            "total_cart_value": sum(product.total for product in products),
        },
    )


@router.get("/checkout")
def get_checkout_form(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    products = get_personalized_retail_product_views_workflow.get_personalized_retail_product_views(
        user_id, only_already_in_cart=True
    )
    return templates.TemplateResponse(
        "retail/checkoutForm.html",
        {
            "request": request,
            "total_cart_value": sum(product.total for product in products),
        },
    )


@router.post("/checkout")
def post_checkout(
    user_id: Annotated[int, Depends(get_current_user_id)],
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    destination_longitude: Annotated[float, Form()],
    destination_latitude: Annotated[float, Form()],
):
    handle_checkout_workflow.handle_checkout(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        destination_longitude=destination_longitude,
        destination_latitude=destination_latitude,
    )
    return RedirectResponse(url=f"/retail/orders", status_code=303)


@router.get("/orders")
def get_orders(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    orders = [
        OrderView(
            id=1,
            price=Decimal(111.0),
            destination_location_latitude=55.0,
            destination_location_longitude=11.0,
            first_name="John",
            last_name="Doe",
            products=[RetailStatusProductView(id=1, label="Smartwatch", count=1)],
            transports=[
                RetailTransportView(
                    transport_id=5,
                    product_label="Smartwatch",
                    product_count=1,
                    transport_status=TransportStatus.COMPLETE,
                )
            ],
            status=OrderStatus.FINISHED,
        )
    ]
    return templates.TemplateResponse(
        "retail/listOrders.html",
        {
            "request": request,
            "orders": orders,
        },
    )


@router.get("/order/{order_id}")
def get_order_view(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    order_id: int,
):
    order = OrderView(
        id=1,
        price=Decimal(111.0),
        destination_location_latitude=55.0,
        destination_location_longitude=11.0,
        first_name="John",
        last_name="Doe",
        products=[RetailStatusProductView(id=1, label="Smartwatch", count=1)],
        transports=[
            RetailTransportView(
                transport_id=5,
                product_label="Smartwatch",
                product_count=1,
                transport_status=TransportStatus.COMPLETE,
            )
        ],
        status=OrderStatus.FINISHED,
    )
    return templates.TemplateResponse(
        "retail/orderView.html",
        {
            "request": request,
            "order": order,
        },
    )
