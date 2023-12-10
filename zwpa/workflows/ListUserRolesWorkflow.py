from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException

from zwpa.model import User, UserRole


@dataclass(eq=True)
class UserRolesView:
    id: int
    login: str
    is_admin: bool = False
    is_clerk: bool = False
    is_client: bool = False
    is_supplier: bool = False
    is_transport: bool = False


class ListUserRolesWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    def list_user_roles_workflow(self, admin_id: int) -> list[UserRolesView]:
        with self.session_maker() as session:
            if not self.__is_user_of_role(
                session, user_id=admin_id, role=UserRole.ADMIN
            ):
                raise UserLacksRoleException()
            return [
                self.__map_user_to_user_roles_view(user)
                for user in session.execute(select(User)).scalars()
            ]

    def __is_user_of_role(self, session: Session, user_id: int, role: UserRole) -> bool:
        user_roles = [
            assignment.role for assignment in session.get_one(User, user_id).roles
        ]
        return role in user_roles

    def __map_user_to_user_roles_view(self, user: User) -> UserRolesView:
        user_roles = [assignment.role for assignment in user.roles]
        return UserRolesView(
            id=user.id,
            login=user.login,
            is_admin=UserRole.ADMIN in user_roles,
            is_clerk=UserRole.CLERK in user_roles,
            is_client=UserRole.CLIENT in user_roles,
            is_supplier=UserRole.SUPPLIER in user_roles,
            is_transport=UserRole.TRANSPORT in user_roles,
        )
