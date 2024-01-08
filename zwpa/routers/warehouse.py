from dataclasses import asdict
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from zwpa.model import TransportStatus, UserRole
from zwpa.workflows.transport.AcceptTransportOfferForRequestWorkflow import (
    AcceptTransportOfferForRequestWorkflow,
)
from zwpa.workflows.transport.ChangeTransportStatusWorkflow import (
    ChangeTransportStatusWorkflow,
)
from zwpa.workflows.transport.CreateTransportOfferForRequestWorkflow import (
    CreateTransportOfferForRequestWorkflow,
)
from zwpa.workflows.transport.GetTransportWorkflow import GetTransportWorkflow
from zwpa.workflows.transport.ListTransportOffersForRequestWorkflow import (
    ListTransportOffersForRequestWorkflow,
)
from zwpa.workflows.transport.ListTransportRequestsWorkflow import (
    ListTransportRequestsWorkflow,
)
from zwpa.workflows.transport.ListTransportsWorkflow import ListTransportWorkflow
from zwpa.workflows.transport.TransportAccessChecker import TransportAccessChecker

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker
from zwpa.workflows.warehouse.GetWarehouseDetailsWorkflow import GetWarehouseDetailsWorkflow
from zwpa.workflows.warehouse.ListAllWarehousesWorkflow import ListAllWarehousesWorkflow
from .shared import get_current_user_id, session_maker, templates


router = APIRouter(
    prefix="/warehouse",
    tags=["warehouse"],
)
user_role_checker = UserRoleChecker(session_maker)
list_warehouses_workflow = ListAllWarehousesWorkflow(session_maker)
get_warehouse_details_workflow = GetWarehouseDetailsWorkflow(session_maker)


@router.get("/all")
def get_all_warehouses(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    warehouses = list_warehouses_workflow.list_all_warehouses(user_id)
    return templates.TemplateResponse(
        "warehouse/listWarehouses.html",
        {
            "request": request,
            "warehouses": [asdict(view) for view in warehouses],
        },
    )

@router.get("/{warehouse_id}")
def get_warehouse_details(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)], warehouse_id: int
):
    warehouse_view = get_warehouse_details_workflow.get_warehouse_details(user_id, warehouse_id)
    return templates.TemplateResponse(
        "warehouse/warehouseDetails.html",
        {
            "request": request,
            "warehouse": asdict(warehouse_view.warehouse),
            "products": [asdict(product) for product in warehouse_view.products],
        },
    )
