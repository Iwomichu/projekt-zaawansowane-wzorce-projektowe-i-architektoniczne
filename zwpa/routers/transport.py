from dataclasses import asdict
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from zwpa.model import UserRole
from zwpa.workflows.transport.CreateTransportOfferForRequestWorkflow import CreateTransportOfferForRequestWorkflow
from zwpa.workflows.transport.ListTransportOffersForRequestWorkflow import ListTransportOffersForRequestWorkflow
from zwpa.workflows.transport.ListTransportRequestsWorkflow import (
    ListTransportRequestsWorkflow,
)

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker
from .shared import get_current_user_id, session_maker, templates


router = APIRouter(
    prefix="/transport",
    tags=["transport"],
)
user_role_checker = UserRoleChecker(session_maker)
list_transport_requests_workflow = ListTransportRequestsWorkflow(session_maker)
create_transport_offer_for_request_workflow = CreateTransportOfferForRequestWorkflow(session_maker)
list_transport_offers_for_request_workflow = ListTransportOffersForRequestWorkflow(session_maker)


@router.get("/requests")
def get_transports(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    transport_requests = (
        list_transport_requests_workflow.list_available_transport_requests(user_id)
    )
    is_transporter = user_role_checker.is_user_of_role(user_id, role=UserRole.TRANSPORT)
    is_clerk = user_role_checker.is_user_of_role(user_id, role=UserRole.CLERK)
    print(transport_requests)
    return templates.TemplateResponse(
        "transport/listAllTransportRequests.html",
        {
            "request": request,
            "is_transporter": is_transporter,
            "is_clerk": is_clerk,
            "transport_requests": [asdict(view) for view in transport_requests],
        },
    )


@router.post("/request/{transport_request_id}/offer")
def post_transport_offer_for_request(request: Request, user_id: Annotated[int, Depends(get_current_user_id)], transport_request_id: int):
    create_transport_offer_for_request_workflow.create_transport_offer_for_request(user_id, transport_request_id)
    return RedirectResponse(url="/transport/requests", status_code=303)


@router.get("/request/{transport_request_id}/offers")
def get_transport_offers_for_request(request: Request, user_id: Annotated[int, Depends(get_current_user_id)], transport_request_id: int):
    transport_offers = list_transport_offers_for_request_workflow.list_transport_offer_for_request(user_id, transport_request_id)
    return templates.TemplateResponse(
        "transport/listTransportOffersForRequest.html",
        {
            "request": request,
            "transport_request_id": transport_request_id,
            "transport_offers": [asdict(view) for view in transport_offers],
        },
    )
