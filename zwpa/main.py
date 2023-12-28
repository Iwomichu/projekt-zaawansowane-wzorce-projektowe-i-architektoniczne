from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing_extensions import Annotated
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse

from zwpa.workflows.user.CreateRootWorkflow import CreateRootWorkflow
from zwpa.workflows.utils.SeedSystemWithData import SeedSystemWithDataWorkflow
from .model import Base
from .routers.shared import (
    session_maker,
    config,
    engine,
    templates,
    get_current_user_id,
)
from .routers.user import (
    router as user_router,
    create_user_workflow,
    modify_user_roles_workflow,
)
from .routers.client_requests import router as client_requests_router
from .routers.supply import router as supply_router
from .routers.transport import router as transport_router


create_root_workflow = CreateRootWorkflow(
    session_maker,
    config=config,
    create_user_workflow=create_user_workflow,
    modify_user_roles_workflow=modify_user_roles_workflow,
)
seed_system_with_data_workflow = SeedSystemWithDataWorkflow(session_maker)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    create_root_workflow.create_root_user()
    seed_system_with_data_workflow.seed()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(user_router)
app.include_router(client_requests_router)
app.include_router(supply_router)
app.include_router(transport_router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "landingPage.html",
        {"request": request, "timestamp": datetime.now(tz=timezone.utc).isoformat()},
    )


@app.get("/login", response_class=HTMLResponse)
def login(request: Request, _: Annotated[int, Depends(get_current_user_id)]):
    return templates.TemplateResponse(
        "landingPage.html",
        {"request": request, "timestamp": datetime.now(tz=timezone.utc).isoformat()},
    )
