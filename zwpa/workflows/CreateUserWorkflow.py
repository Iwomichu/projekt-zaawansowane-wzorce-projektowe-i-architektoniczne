from zwpa.model import User
from zwpa.types import McfHash
from zwpa.exceptions.UserAlreadyExistsException import UserAlreadyExistsException
from zwpa.model import LOGIN_ATTEMPTS


import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker


class CreateUserWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    def create_user(self, login: str, plain_text_password: str) -> int:
        with self.session_maker() as session:
            if self._user_exists(session, login=login):
                raise UserAlreadyExistsException(login)

            user = User(
                login=login,
                password=self._hash_password(plain_text_password),
                login_attempts_left=LOGIN_ATTEMPTS
            )
            session.add(user)
            session.commit()
            user_id = user.id
        return user_id

    def _user_exists(self, session: Session, login: str) -> bool:
        return session.scalars(select(User).filter_by(login=login)).first() is not None

    def _hash_password(self, plain_text_password: str) -> McfHash:
        return McfHash(bcrypt.hashpw(plain_text_password.encode(encoding="utf-8"), salt=bcrypt.gensalt()))