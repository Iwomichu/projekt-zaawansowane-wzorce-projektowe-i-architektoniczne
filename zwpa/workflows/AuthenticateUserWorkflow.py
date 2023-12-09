from zwpa.model import User
from zwpa.types import McfHash
from zwpa.model import UserAuthenticationLogRecord
from zwpa.UserAuthenticationResult import UserAuthenticationResult
from zwpa.exceptions.UserDoesNotExist import UserDoesNotExist
from zwpa.exceptions.UserHasDifferentPassword import UserHasDifferentPassword
from zwpa.exceptions.UserHasNoLoginAttemptsLeft import UserHasNoLoginAttemptsLeft
from zwpa.model import LOGIN_ATTEMPTS


import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker


from typing import Optional


class AuthenticateUserWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    def authenticate_user(self, login: str, plain_text_password: str) -> UserAuthenticationResult:
        authenticated = False
        try:
            with self.session_maker() as session:
                user = self._get_user(session, login=login)

                if user is None:
                    raise UserDoesNotExist(user_login=login)

                if user.login_attempts_left < 1:
                    raise UserHasNoLoginAttemptsLeft(user_login=user.login, authentication_result=UserAuthenticationResult(authenticated=False))

                if not self._passwords_match(plain_text_password=plain_text_password, hashed_password=user.password):
                    user.login_attempts_left -= 1
                    session.commit()
                    raise UserHasDifferentPassword(user_login=user.login, authentication_result=UserAuthenticationResult(authenticated=False))

                user.login_attempts_left = LOGIN_ATTEMPTS
                session.commit()

                authenticated = True
                return UserAuthenticationResult(authenticated=True)
        finally:
            # Extremaly risky, since finally will overwrite the exception if raises
            with self.session_maker() as session:
                session.add(UserAuthenticationLogRecord(login=login, authenticated=authenticated))
                session.commit()


    def _get_user(self, session: Session, login: str) -> Optional[User]:
        return session.scalars(select(User).filter_by(login=login)).one_or_none()

    def _passwords_match(self, plain_text_password: str, hashed_password: McfHash) -> bool:
        return bcrypt.checkpw(password=plain_text_password.encode("utf-8"), hashed_password=hashed_password)