from sqlalchemy.orm import sessionmaker, Session

from zwpa.config import Config
from zwpa.exceptions.UserAlreadyExistsException import UserAlreadyExistsException
from zwpa.model import UserRole
from zwpa.workflows.CreateUserWorkflow import CreateUserWorkflow
from zwpa.workflows.ModifyUserRolesWorkflow import ModifyUserRolesWorkflow


class CreateRootWorkflow:
    def __init__(self, session_maker: sessionmaker, config: Config, create_user_workflow: CreateUserWorkflow, modify_user_roles_workflow: ModifyUserRolesWorkflow) -> None:
        self.session_maker = session_maker
        self.config = config
        self.create_user_workflow = create_user_workflow
        self.modify_user_roles_workflow = modify_user_roles_workflow

    def create_root_user(self) -> None:
        try:
            root_id = self.create_user_workflow.create_user(self.config.admin_login, self.config.admin_password)
            self.modify_user_roles_workflow.modify_user_roles(root_id, roles=list(UserRole))
        except UserAlreadyExistsException as e:
            print("Root account already present. Account creation aborted")