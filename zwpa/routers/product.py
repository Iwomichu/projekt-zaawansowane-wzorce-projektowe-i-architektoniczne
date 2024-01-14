from dataclasses import asdict
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from zwpa.workflows.product.HandleProductDetailsWorkflow import (
    HandleProductDetailsWorkflow,
)
from zwpa.workflows.product.ListProductsWorkflow import ListProductsWorkflow

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker
from .shared import get_current_user_id, session_maker, templates


router = APIRouter(
    prefix="/product",
    tags=["product"],
)
user_role_checker = UserRoleChecker(session_maker)
list_products_workflow = ListProductsWorkflow(session_maker)
handle_product_details_workflow = HandleProductDetailsWorkflow(session_maker)


@router.get("/all")
def get_all_products(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    products = list_products_workflow.list_products(user_id)
    return templates.TemplateResponse(
        "product/listProducts.html",
        {
            "request": request,
            "products": [asdict(product) for product in products]
            # "products": [
            #     {
            #         "id": 1,
            #         "label": "Smartphone",
            #         "unit": "ISO_CONTAINER",
            #         "retail_price": 8.99,
            #         "mean_sell_bulk_price": 7.39,
            #         "mean_buy_bulk_price": 5.31,
            #         "amount_in_our_warehouses": 123,
            #         "amount_incoming_to_our_warehouses": 21,
            #         "amount_requested_by_us": 22,
            #         "amount_requested_by_clients": 40,
            #     }
            # ],
        },
    )


@router.get("/{product_id}")
def get_warehouse_details(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    product_id: int,
):
    product_view = handle_product_details_workflow.get_product_details(
        user_id, product_id
    )
    return templates.TemplateResponse(
        "product/productDetails.html",
        {
            "request": request,
            "product": asdict(product_view)
            # "product": {
            #     "id": 1,
            #     "label": "Smartphone",
            #     "unit": "ISO_CONTAINER",
            #     "retail_price": 8.99,
            #     "mean_sell_bulk_price": 7.39,
            #     "mean_buy_bulk_price": 5.31,
            #     "amount_in_our_warehouses": 123,
            #     "amount_incoming_to_our_warehouses": 21,
            #     "amount_requested_by_us": 22,
            #     "amount_requested_by_clients": 40,
            # },
        },
    )


@router.post("/{product_id}")
def post_warehouse_details(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    product_id: int,
    label: Annotated[str, Form()],
    retail_price: Annotated[Decimal, Form()],
):
    handle_product_details_workflow.modify_product_details(
        user_id, product_id, label, retail_price
    )
    return RedirectResponse(url="/product/all", status_code=303)
