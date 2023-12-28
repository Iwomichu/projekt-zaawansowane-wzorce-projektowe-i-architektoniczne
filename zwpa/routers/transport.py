from dataclasses import asdict
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from zwpa.model import UserRole
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


@router.get("/requests")
def get_transports(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    transport_requests = (
        list_transport_requests_workflow.list_available_transport_requests(user_id)
    )
    is_transporter = user_role_checker.is_user_of_role(user_id, role=UserRole.TRANSPORT)
    is_clerk = user_role_checker.is_user_of_role(user_id, role=UserRole.CLERK)
    return templates.TemplateResponse(
        "listAllTransportRequests.html",
        {
            "request": request,
            "is_transporter": is_transporter,
            "is_clerk": is_clerk,
            "transport_requests": [asdict(view) for view in transport_requests],
        },
    )
