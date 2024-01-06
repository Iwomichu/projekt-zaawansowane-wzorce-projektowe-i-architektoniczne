from dataclasses import asdict
from datetime import date, time
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from zwpa.model import UserRole
from zwpa.workflows.supplies.AcceptRequestedSupplyOfferWorkflow import (
    AcceptRequestedSupplyOfferWorkflow,
)
from zwpa.workflows.supplies.CreateNewSupplyOfferWorkflow import (
    CreateNewSupplyOfferWorkflow,
)
from zwpa.workflows.supplies.CreateNewSupplyRequestWorkflow import (
    CreateNewSupplyRequestWorkflow,
)

from zwpa.workflows.supplies.HandleSupplyRequestFormWorkflow import (
    HandleSupplyRequestFormWorkflow,
)
from zwpa.workflows.supplies.ListSupplyOffersForRequestWorkflow import (
    ListSupplyOffersForRequestWorkflow,
)
from zwpa.workflows.supplies.ListSupplyRequestsWorkflow import (
    ListSupplyRequestsWorkflow,
)
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker
from .shared import get_current_user_id, session_maker, templates

router = APIRouter(
    prefix="/supply",
    tags=["supply"],
)
user_role_checker = UserRoleChecker(session_maker)
list_supply_requests_workflow = ListSupplyRequestsWorkflow(session_maker)
handle_supply_request_form_workflow = HandleSupplyRequestFormWorkflow(session_maker)
create_new_supply_request_workflow = CreateNewSupplyRequestWorkflow(session_maker)
create_new_supply_offer_workflow = CreateNewSupplyOfferWorkflow(session_maker)
list_supply_offers_for_request_workflow = ListSupplyOffersForRequestWorkflow(
    session_maker
)
accept_supply_offer_for_request_workflow = AcceptRequestedSupplyOfferWorkflow(
    session_maker
)


@router.get("/requests")
def get_list_supply_requests(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    supply_requests = list_supply_requests_workflow.list_supply_requests(user_id)
    is_supplier = user_role_checker.is_user_of_role(user_id, role=UserRole.SUPPLIER)
    is_clerk = user_role_checker.is_user_of_role(user_id, role=UserRole.CLERK)
    return templates.TemplateResponse(
        "supply/listSupplyRequests.html",
        {
            "request": request,
            "is_supplier": is_supplier,
            "is_clerk": is_clerk,
            "supply_requests": [asdict(view) for view in supply_requests],
        },
    )


@router.get("/request/create")
def get_create_supply_request(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    supply_request_form_data = handle_supply_request_form_workflow.get_data(user_id)
    return templates.TemplateResponse(
        "supply/createSupplyRequestPage.html",
        {"request": request, "data": asdict(supply_request_form_data)},
    )


@router.post("/request/create")
def post_create_supply_request(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    warehouse_id: Annotated[int, Form()],
    product_id: Annotated[int, Form()],
    time_window_id: Annotated[int, Form()],
    unit_count: Annotated[int, Form()],
    request_deadline: Annotated[date, Form()],
):
    create_new_supply_request_workflow.create_new_supply_request(
        user_id=user_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        time_window_id=time_window_id,
        unit_count=unit_count,
        request_deadline=request_deadline,
    )
    return RedirectResponse(url="/supply/requests", status_code=303)


@router.get("/request/{supply_request_id}/offer/create")
def get_create_supply_offer(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    supply_request_id: int,
):
    user_role_checker.assert_user_of_role(user_id, role=UserRole.SUPPLIER)
    return templates.TemplateResponse(
        "supply/createSupplyOfferPage.html",
        {"request": request, "supply_request_id": supply_request_id},
    )


@router.post("/request/{supply_request_id}/offer/create")
def post_create_supply_ofer(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    supply_request_id: int,
    price: Annotated[Decimal, Form()],
    transport_deadline: Annotated[date, Form()],
    source_longitude: Annotated[int, Form()],
    source_latitude: Annotated[int, Form()],
    load_time_window_start: Annotated[time, Form()],
    load_time_window_end: Annotated[time, Form()],
):
    create_new_supply_offer_workflow.create_new_supply_offer_for_request(
        price=price,
        transport_deadline=transport_deadline,
        supply_request_id=supply_request_id,
        supplier_id=user_id,
        load_time_window_start=load_time_window_start,
        load_time_window_end=load_time_window_end,
        source_longitude=source_longitude,
        source_latitude=source_latitude,
    )
    return RedirectResponse(url="/supply/requests", status_code=303)


@router.get("/request/{supply_request_id}/offers")
def get_supply_offers_for_request(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    supply_request_id: int,
):
    supply_offers = (
        list_supply_offers_for_request_workflow.list_supply_offers_for_request(
            user_id, supply_request_id=supply_request_id
        )
    )
    return templates.TemplateResponse(
        "supply/listSupplyOffersForRequest.html",
        {
            "request": request,
            "supply_request_id": supply_request_id,
            "supply_offers": [asdict(view) for view in supply_offers],
        },
    )


@router.get("/request/{supply_request_id}/offer/{supply_offer_id}/accept")
def get_accept_supply_offer_for_request(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    supply_request_id: int,
    supply_offer_id: int,
):
    user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
    return templates.TemplateResponse(
        "supply/acceptSupplyOfferForRequest.html",
        {
            "request": request,
            "supply_request_id": supply_request_id,
            "supply_offer_id": supply_offer_id,
        },
    )


@router.post("/request/{supply_request_id}/offer/{supply_offer_id}/accept")
def post_accept_supply_offer_for_request(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    supply_request_id: int,
    supply_offer_id: int,
    transport_request_deadline: Annotated[date, Form()],
    price_for_transport: Annotated[Decimal, Form()],
):
    accept_supply_offer_for_request_workflow.accept_supply_offer(
        supply_offer_id=supply_offer_id,
        user_id=user_id,
        transport_price=price_for_transport,
        transport_request_deadline=transport_request_deadline,
    )
    return RedirectResponse(url="/supply/requests", status_code=303)
