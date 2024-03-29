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
from .shared import get_current_user_id, session_maker, templates


router = APIRouter(
    prefix="/transport",
    tags=["transport"],
)
user_role_checker = UserRoleChecker(session_maker)
transport_access_checker = TransportAccessChecker(session_maker)
list_transports_workflow = ListTransportWorkflow(session_maker)
list_transport_requests_workflow = ListTransportRequestsWorkflow(session_maker)
create_transport_offer_for_request_workflow = CreateTransportOfferForRequestWorkflow(
    session_maker
)
list_transport_offers_for_request_workflow = ListTransportOffersForRequestWorkflow(
    session_maker
)
accept_transport_offer_for_request_workflow = AcceptTransportOfferForRequestWorkflow(
    session_maker
)
get_transport_workflow = GetTransportWorkflow(session_maker)
change_transport_status_workflow = ChangeTransportStatusWorkflow(session_maker)


@router.get("/transports")
def get_all_transports(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    transports = list_transports_workflow.list_all_transports(user_id)
    return templates.TemplateResponse(
        "transport/listTransports.html",
        {
            "request": request,
            "transports": [asdict(view) for view in transports],
        },
    )


@router.get("/transport/{transport_id}")
def get_transport(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    transport_id: int,
):
    transport = get_transport_workflow.get_transport(user_id, transport_id)
    is_transporter_of_this_transport = (
        transport_access_checker.is_transporter_of_this_transport(user_id, transport_id)
    )
    return templates.TemplateResponse(
        "transport/transportView.html",
        {
            "request": request,
            "transport": asdict(transport),
            "is_transporter_of_this_transport": is_transporter_of_this_transport,
        },
    )


@router.post("/transport/{transport_id}/status/loaded")
def post_transport_status_loaded(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    transport_id: int,
):
    change_transport_status_workflow.change_transport_status(
        user_id, transport_id, new_status=TransportStatus.IN_TRANSIT
    )
    return RedirectResponse(url=f"/transport/transport/{transport_id}", status_code=303)


@router.post("/transport/{transport_id}/status/delivered")
def post_transport_status_delivered(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    transport_id: int,
):
    change_transport_status_workflow.change_transport_status(
        user_id, transport_id, new_status=TransportStatus.COMPLETE
    )
    return RedirectResponse(url=f"/transport/transport/{transport_id}", status_code=303)


@router.get("/requests")
def get_transport_requests(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    transport_requests = (
        list_transport_requests_workflow.list_available_transport_requests(user_id)
    )
    is_transporter = user_role_checker.is_user_of_role(user_id, role=UserRole.TRANSPORT)
    is_clerk = user_role_checker.is_user_of_role(user_id, role=UserRole.CLERK)
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
def post_transport_offer_for_request(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    transport_request_id: int,
):
    create_transport_offer_for_request_workflow.create_transport_offer_for_request(
        user_id, transport_request_id
    )
    return RedirectResponse(url="/transport/requests", status_code=303)


@router.get("/request/{transport_request_id}/offers")
def get_transport_offers_for_request(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    transport_request_id: int,
):
    transport_offers = (
        list_transport_offers_for_request_workflow.list_transport_offer_for_request(
            user_id, transport_request_id
        )
    )
    return templates.TemplateResponse(
        "transport/listTransportOffersForRequest.html",
        {
            "request": request,
            "transport_request_id": transport_request_id,
            "transport_offers": [asdict(view) for view in transport_offers],
        },
    )


@router.post("/request/{transport_request_id}/offer/{transport_offer_id}/accept")
def post_accept_transport_offer_for_request(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    transport_request_id: int,
    transport_offer_id: int,
):
    accept_transport_offer_for_request_workflow.accept_transport_offer_for_request(
        user_id, transport_offer_id, transport_request_id
    )
    return RedirectResponse(url="/transport/requests", status_code=303)
