from sqlalchemy.orm import Session
from zwpa.model import UserRole
from zwpa.model import UserRoleAssignment

from zwpa.model import User


class Fixtures:
    current_id_counter: int = 0

    @classmethod
    def next_id(cls) -> int:
        cls.current_id_counter += 1
        return cls.current_id_counter

    @classmethod
    def new_user(
        cls,
        session: Session,
        id: int | None = None,
        login: str = "user",
        password: bytes = b"password",
        login_attempts_left: int = 3,
    ) -> User:
        user = User(
            id=id if id is not None else cls.next_id(),
            login=login,
            password=password,
            login_attempts_left=login_attempts_left,
        )
        session.add(user)
        return user

    @classmethod
    def new_role_assignment(
        cls,
        session: Session,
        role: UserRole,
        user_id: int,
        id: int = 1,
    ) -> UserRoleAssignment:
        user_role_assignment = UserRoleAssignment(
            role=role, user_id=user_id, id=id if id is not None else cls.next_id()
        )
        session.add(user_role_assignment)
        return user_role_assignment
