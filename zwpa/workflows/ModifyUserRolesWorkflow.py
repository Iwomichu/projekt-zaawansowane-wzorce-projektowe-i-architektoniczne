from sqlalchemy.orm import sessionmaker, Session
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException
from zwpa.model import User, UserRole, UserRoleAssignment


class ModifyUserRolesWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    def modify_user_roles_as_admin(
        self, admin_id: int, user_id: int, roles: list[UserRole]
    ) -> None:
        with self.session_maker() as session:
            if not self.__is_user_of_role(session, admin_id, UserRole.ADMIN):
                raise UserLacksRoleException()
            self.modify_user_roles(user_id, roles)
            session.commit()

    def modify_user_roles(self, user_id: int, roles: list[UserRole]) -> None:
        with self.session_maker() as session:
            for role in roles:
                self.__grant_role_to_user(session, user_id, role)
            session.commit()
            

    def __is_user_of_role(self, session: Session, user_id: int, role: UserRole) -> bool:
        user_roles = [
            assignment.role for assignment in session.get_one(User, user_id).roles
        ]
        return role in user_roles
    
    def __grant_role_to_user(self, session: Session, user_id: int, role: UserRole) -> None:
        user_role_assignment = UserRoleAssignment(role=role, user_id=user_id)
        session.add(user_role_assignment)
