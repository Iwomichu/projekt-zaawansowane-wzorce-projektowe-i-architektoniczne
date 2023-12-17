from dataclasses import asdict
from datetime import date, time
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException
from zwpa.workflows.client_requests.AcceptClientRequestWorkflow import AcceptClientRequestWorkflow
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import (
    AddNewClientRequestWorkflow,
)

from zwpa.workflows.client_requests.GetClientRequestsWorkflow import (
    GetClientRequestsWorkflow,
)
from zwpa.workflows.client_requests.HandleClientRequestAcceptanceFormWorkflow import HandleClientRequestAcceptanceFormWorkflow
from zwpa.workflows.client_requests.HandleClientRequestFormWorkflow import (
    HandleClientRequestFormWorkflow,
)
from .shared import get_current_user_id, session_maker, templates, config

router = APIRouter(
    prefix="/client_requests",
    tags=["client_requests"],
)
get_client_requests_workflow = GetClientRequestsWorkflow(session_maker)
handle_client_request_form_workflow = HandleClientRequestFormWorkflow(session_maker)
add_new_client_request_workflow = AddNewClientRequestWorkflow(
    session_maker, min_days_to_process=config.min_days_to_proceed
)
handle_client_request_acceptance_form_workflow = HandleClientRequestAcceptanceFormWorkflow(session_maker)
accept_client_request_workflow = AcceptClientRequestWorkflow(session_maker)


@router.get("/my")
def my_client_requests(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    try:
        request_views = get_client_requests_workflow.get_my_client_requests_workflow(
            user_id
        )
        return templates.TemplateResponse(
            "listOwnClientRequestsPage.html",
            {
                "request": request,
                "client_requests": [asdict(view) for view in request_views],
            },
        )
    except UserLacksRoleException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.get("/all")
def all_client_requests(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    try:
        request_views = get_client_requests_workflow.get_all_client_requests_workflow(
            user_id
        )
        return templates.TemplateResponse(
            "listAllClientRequestsPage.html",
            {
                "request": request,
                "client_requests": [asdict(view) for view in request_views],
            },
        )
    except UserLacksRoleException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.get("/create")
def get_client_request_form(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    product_views = (
        handle_client_request_form_workflow.get_client_request_form_init_data(user_id)
    )
    return templates.TemplateResponse(
        "createClientRequestPage.html",
        {"request": request, "products": [asdict(view) for view in product_views]},
    )


@router.post("/create")
def post_client_request_form(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    price: Annotated[Decimal, Form()],
    unit_count: Annotated[int, Form()],
    request_deadline: Annotated[date, Form()],
    transport_deadline: Annotated[date, Form()],
    destination_longitude: Annotated[float, Form()],
    destination_latitude: Annotated[float, Form()],
    supply_time_window_start: Annotated[time, Form()],
    supply_time_window_end: Annotated[time, Form()],
    product: Annotated[int, Form()],
):
    add_new_client_request_workflow.add_new_client_request(
        user_id=user_id,
        price=price,
        unit_count=unit_count,
        request_deadline=request_deadline,
        transport_deadline=transport_deadline,
        product_id=product,
        supply_time_window=(supply_time_window_start, supply_time_window_end),
        destination=(destination_longitude, destination_latitude),
    )
    return RedirectResponse(url="/client_requests/my", status_code=303)


@router.get("/accept")
def get_accept_client_request_form(request: Request, client_request_id: int, user_id: Annotated[int, Depends(get_current_user_id)]):
    client_request_acceptance_form_data = handle_client_request_acceptance_form_workflow.get_form_data(user_id, client_request_id)
    return templates.TemplateResponse(
        "acceptClientRequestPage.html",
        {"request": request, "data": asdict(client_request_acceptance_form_data)},
    )
