from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException

from zwpa.workflows.GetClientRequestsWorkflow import GetClientRequestsWorkflow
from .shared import get_current_user_id, session_maker

router = APIRouter(
    prefix="/client_requests",
    tags=["client_requests"],
)
get_client_requests_workflow = GetClientRequestsWorkflow(session_maker)


@router.get("/my")
def my_client_requests(user_id: Annotated[int, Depends(get_current_user_id)]):
    try:
        return get_client_requests_workflow.get_my_client_requests_workflow(user_id)
    except UserLacksRoleException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.get("/all")
def all_client_requests(user_id: Annotated[int, Depends(get_current_user_id)]):
    try:
        return get_client_requests_workflow.get_all_client_requests_workflow(user_id)
    except UserLacksRoleException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
