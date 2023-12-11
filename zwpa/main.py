from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from typing_extensions import Annotated
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException

from zwpa.workflows.AuthenticateUserWorkflow import AuthenticateUserWorkflow
from zwpa.workflows.GetClientRequestsWorkflow import GetClientRequestsWorkflow
from zwpa.workflows.ListUserRolesWorkflow import ListUserRolesWorkflow
from .config import Config
from .model import Base, UserRole

from .workflows.CreateUserWorkflow import CreateUserWorkflow
from .workflows.ModifyUserRolesWorkflow import ModifyUserRolesWorkflow


config = Config.from_environmental_variables()
engine = create_engine(
    URL.create(
        "postgresql",
        username=config.database.login,
        password=config.database.password,
        host=config.database.host,
        database=config.database.database,
        port=config.database.port,
    )
)
session_maker = sessionmaker(engine)
create_user_workflow = CreateUserWorkflow(session_maker)
modify_user_roles_workflow = ModifyUserRolesWorkflow(session_maker)
authenticate_user_workflow = AuthenticateUserWorkflow(session_maker)
get_client_requests_workflow = GetClientRequestsWorkflow(session_maker)
list_user_roles_workflow = ListUserRolesWorkflow(session_maker)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    admin_id = create_user_workflow.create_user(
        config.admin_login, config.admin_password
    )
    modify_user_roles_workflow.modify_user_roles(admin_id, list(UserRole))
    yield


app = FastAPI(lifespan=lifespan)
security = HTTPBasic()
templates = Jinja2Templates(directory="templates")


def get_current_user_id(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    result = authenticate_user_workflow.authenticate_user(
        credentials.username, credentials.password
    )
    if not result.authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return result.user_id


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "landingPage.html",
        {"request": request, "timestamp": datetime.now(tz=timezone.utc).isoformat()},
    )


@app.get("/user/create")
def get_create_user(request: Request):
    return templates.TemplateResponse(
        "createAccountPage.html",
        {"request": request},
    )


@app.post("/user/create")
def post_create_user(
    request: Request, login: Annotated[str, Form()], password: Annotated[str, Form()]
):
    create_user_workflow.create_user(login, plain_text_password=password)
    return templates.TemplateResponse(
        "accountCreatedPage.html",
        {"request": request},
    )


@app.get("/user/roles")
def get_user_roles(
    request: Request, user_id: Annotated[int, Depends(get_current_user_id)]
):
    user_roles_views = list_user_roles_workflow.list_user_roles_workflow(user_id)
    return templates.TemplateResponse(
        "userRolesPage.html",
        {"request": request, "users": [asdict(view) for view in user_roles_views]},
    )


@app.get("/user/roles/edit")
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


@app.post("/user/roles/edit")
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
    modify_user_roles_workflow.modify_user_roles_as_admin(admin_id=user_id, user_id=target_id, roles=user_roles)
    
    user_roles_views = list_user_roles_workflow.list_user_roles_workflow(user_id)
    return templates.TemplateResponse(
        "userRolesPage.html",
        {"request": request, "users": [asdict(view) for view in user_roles_views]},
    )


@app.get("/login")
def get_login(request: Request, user_id: Annotated[int, Depends(get_current_user_id)]):
    return templates.TemplateResponse(
        "personalizedLandingPage.html",
        {
            "request": request,
            "id": user_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
    )


@app.get("/client_requests/my")
def my_client_requests(user_id: Annotated[int, Depends(get_current_user_id)]):
    try:
        return get_client_requests_workflow.get_my_client_requests_workflow(user_id)
    except UserLacksRoleException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.get("/client_requests/all")
def all_client_requests(user_id: Annotated[int, Depends(get_current_user_id)]):
    try:
        return get_client_requests_workflow.get_all_client_requests_workflow(user_id)
    except UserLacksRoleException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
