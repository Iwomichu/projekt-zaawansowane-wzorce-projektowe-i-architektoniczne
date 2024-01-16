from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from zwpa.config import Config
from zwpa.workflows.retail.RestCartManager import RestCartManager
from zwpa.workflows.user.AuthenticateUserWorkflow import AuthenticateUserWorkflow


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
security = HTTPBasic()
templates = Jinja2Templates(directory="templates")
rest_cart_manager = RestCartManager(
    manager_url=config.cart_manager_config.url,
    manager_access_key=config.cart_manager_config.access_key,
)

authenticate_user_workflow = AuthenticateUserWorkflow(session_maker)


def get_current_user_id(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    result = authenticate_user_workflow.authenticate_user(
        credentials.username, credentials.password
    )
    if not result.authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return result.user_id