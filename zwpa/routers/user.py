
from dataclasses import asdict
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request
from zwpa.model import UserRole
from zwpa.workflows.user.AuthenticateUserWorkflow import AuthenticateUserWorkflow

from zwpa.workflows.user.CreateUserWorkflow import CreateUserWorkflow
from zwpa.workflows.user.ListUserRolesWorkflow import ListUserRolesWorkflow
from zwpa.workflows.user.ModifyUserRolesWorkflow import ModifyUserRolesWorkflow
from .shared import get_current_user_id, session_maker, templates

router = APIRouter(
    prefix="/user",
    tags=["user"],
)
create_user_workflow = CreateUserWorkflow(session_maker)
modify_user_roles_workflow = ModifyUserRolesWorkflow(session_maker)
authenticate_user_workflow = AuthenticateUserWorkflow(session_maker)
list_user_roles_workflow = ListUserRolesWorkflow(session_maker)


@router.get("/create")
def get_create_user(request: Request):
    return templates.TemplateResponse(
        "createAccountPage.html",
        {"request": request},
    )


@router.post("/create")
def post_create_user(
    request: Request, login: Annotated[str, Form()], password: Annotated[str, Form()]
):
    create_user_workflow.create_user(login, plain_text_password=password)
    return templates.TemplateResponse(
        "accountCreatedPage.html",
        {"request": request},
    )


@router.get("/roles")
def get_user_roles(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    user_roles_views = list_user_roles_workflow.list_user_roles_workflow(user_id)
    return templates.TemplateResponse(
        "userRolesPage.html",
        {"request": request, "users": [asdict(view) for view in user_roles_views]},
    )


@router.get("/roles/edit")
def get_user_roles_update_form(
    target_id: int,
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    user_roles_view = list_user_roles_workflow.get_single_user_role_view_workflow(
        admin_id=user_id, user_id=target_id
    )
    return templates.TemplateResponse(
        "editUserRolesPage.html",
        {"request": request, "user": user_roles_view},
    )


@router.post("/roles/edit")
def post_user_roles_update_form(
    target_id: int,
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    is_admin: Annotated[bool, Form()] = False,
    is_client: Annotated[bool, Form()] = False,
    is_clerk: Annotated[bool, Form()] = False,
    is_supplier: Annotated[bool, Form()] = False,
    is_transport: Annotated[bool, Form()] = False,
):
    user_roles = []

    if is_admin:
        user_roles.append(UserRole.ADMIN)
    if is_clerk:
        user_roles.append(UserRole.CLERK)
    if is_client:
        user_roles.append(UserRole.CLIENT)
    if is_supplier:
        user_roles.append(UserRole.SUPPLIER)
    if is_transport:
        user_roles.append(UserRole.TRANSPORT)
    modify_user_roles_workflow.modify_user_roles_as_admin(
        admin_id=user_id, user_id=target_id, roles=user_roles
    )

    user_roles_views = list_user_roles_workflow.list_user_roles_workflow(user_id)
    return templates.TemplateResponse(
        "userRolesPage.html",
        {"request": request, "users": [asdict(view) for view in user_roles_views]},
    )
