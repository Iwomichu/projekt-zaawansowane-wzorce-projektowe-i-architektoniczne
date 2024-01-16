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
from zwpa.workflows.retail.OrderView import OrderStatus, OrderView
from zwpa.workflows.retail.RetailProductView import (
    PersonalizedRetailProductView,
)
from zwpa.workflows.retail.RetailStatusProductView import RetailStatusProductView
from zwpa.workflows.retail.RetailTransportView import RetailTransportView

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker
from .shared import get_current_user_id, session_maker, templates


router = APIRouter(
    prefix="/retail",
    tags=["retail"],
)
user_role_checker = UserRoleChecker(session_maker)
list_products_workflow = ListProductsWorkflow(session_maker)
handle_product_details_workflow = HandleProductDetailsWorkflow(session_maker)


class RetailSection(str, Enum):
    LIST = "LIST"
    CART = "CART"


@router.get("/")
def get_product_list(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    query: str | None = None,
):
    print(f"Searching for products with {query=}...")
    products = [
        PersonalizedRetailProductView(
            1,
            "Smartwatch",
            "ISO_CONTAINER",
            Decimal(3.11),
            available=5,
            already_in_cart=2,
        ),
        PersonalizedRetailProductView(
            2, "Phone", "ISO_CONTAINER", Decimal(11.33), available=0, already_in_cart=0
        ),
    ]
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
    target_section = "/retail"
    if previous_section is RetailSection.CART:
        target_section += "/cart"
    return RedirectResponse(url=target_section, status_code=303)


@router.get("/cart")
def get_cart(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    cart = [
        PersonalizedRetailProductView(
            1,
            "Smartwatch",
            "ISO_CONTAINER",
            Decimal(3.11),
            available=5,
            already_in_cart=2,
        ),
    ]
    return templates.TemplateResponse(
        "retail/cartView.html",
        {
            "request": request,
            "products": [asdict(product) for product in cart],
            "total_cart_value": sum(product.total for product in cart),
        },
    )


@router.get("/checkout")
def get_checkout_form(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    cart = [
        PersonalizedRetailProductView(
            1,
            "Smartwatch",
            "ISO_CONTAINER",
            Decimal(3.11),
            available=5,
            already_in_cart=2,
        ),
    ]
    return templates.TemplateResponse(
        "retail/checkoutForm.html",
        {
            "request": request,
            "total_cart_value": sum(product.total for product in cart),
        },
    )


@router.post("/checkout")
def post_checkout(
    user_id: Annotated[int, Depends(get_current_user_id)],
):
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
