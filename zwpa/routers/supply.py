from dataclasses import asdict
from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from zwpa.workflows.supplies.CreateNewSupplyRequestWorkflow import CreateNewSupplyRequestWorkflow

from zwpa.workflows.supplies.HandleSupplyRequestFormWorkflow import (
    HandleSupplyRequestFormWorkflow,
)
from .shared import get_current_user_id, session_maker, templates

router = APIRouter(
    prefix="/supply",
    tags=["supply"],
)
handle_supply_request_form_workflow = HandleSupplyRequestFormWorkflow(session_maker)
create_new_supply_request_workflow = CreateNewSupplyRequestWorkflow(session_maker)


@router.get("/request/create")
def get_create_supply_request(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    supply_request_form_data = handle_supply_request_form_workflow.get_data(user_id)
    return templates.TemplateResponse(
        "createSupplyRequestPage.html",
        {"request": request, "data": asdict(supply_request_form_data)},
    )


@router.post("/request/create")
def post_create_supply_request(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)],
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
