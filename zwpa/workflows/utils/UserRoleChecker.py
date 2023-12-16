from sqlalchemy.orm import sessionmaker, Session
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException

from zwpa.model import User, UserRole


class UserRoleChecker:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    def is_user_of_role(self, session: Session, user_id: int, role: UserRole) -> bool:
        user_roles = [
            assignment.role for assignment in session.get_one(User, user_id).roles
        ]
        return role in user_roles
    
    def assert_user_of_role(self, user_id: int, role: UserRole):
        with self.session_maker() as session:
            if not self.is_user_of_role(session, user_id, role):
                raise UserLacksRoleException
