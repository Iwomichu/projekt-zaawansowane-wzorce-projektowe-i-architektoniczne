from sqlalchemy.orm import sessionmaker, Session
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException

from zwpa.model import User, UserRole


class UserRoleChecker:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker

    def is_user_of_role(self, user_id: int, role: UserRole) -> bool:
        with self.session_maker() as session:
            user_roles = [
                assignment.role for assignment in session.get_one(User, user_id).roles
            ]
            return role in user_roles

    def assert_user_of_role(self, user_id: int, role: UserRole):
        self.assert_user_with_one_of_roles(user_id, [role])

    def assert_user_with_one_of_roles(self, user_id: int, roles: list[UserRole]):
        if not any(self.is_user_of_role(user_id, role) for role in roles):
            raise UserLacksRoleException
