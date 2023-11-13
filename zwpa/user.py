from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, NewType
from sqlalchemy import Boolean, Integer, MetaData, String, LargeBinary
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import ENUM as pgEnum


McfHash = NewType("McfHash", str)
LOGIN_ATTEMPTS = 3
metadata = MetaData()

class Base(DeclarativeBase):
    metadata = metadata



class AppSection(str, Enum):
    PRODUCTION = "PRODUCTION"
    TRANSPORT = "TRANSPORT"
    BULK_SALE = "BULK_SALE"


AppSectionType: pgEnum = pgEnum(
    AppSection,
    name="app_section",
    create_constraint=True,
    metadata=Base.metadata,
    validate_strings=True,
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String, index=True)
    password: Mapped[McfHash] = mapped_column(LargeBinary)
    login_attempts_left: Mapped[int] = mapped_column(Integer)


class UserAuthenticationResult(Base):
    __tablename__ = "user_authentication_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String, index=True)
    authenticated: Mapped[bool] = mapped_column(Boolean)


class UserAuthorizationResult:
    __tablename__ = "user_authorization_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String, index=True)
    authorized: Mapped[bool] = mapped_column(Boolean)
    section = mapped_column(AppSectionType)


class UserAlreadyExistsException(Exception):
    def __init__(self, user_login: str) -> None:
        super().__init__(f"User '{user_login=}' already taken")


class UserDoesNotExist(Exception):
    def __init__(self, user_login: str) -> None:
        super().__init__(f"User '{user_login=}' does not exist")


class UserHasDifferentPassword(Exception):
    def __init__(self, user_login: str, authentication_result: UserAuthenticationResult) -> None:
        self.authentication_result = authentication_result
        super().__init__(f"User '{user_login=}' has different password")


class UserHasNoLoginAttemptsLeft(Exception):
    def __init__(self, user_login: str, authentication_result: UserAuthenticationResult) -> None:
        self.authentication_result = authentication_result
        super().__init__(f"User '{user_login=}' has no logging attempts left")


class CreateUserWorkflow:
    def create_user(self, login: str, plain_text_password: str) -> None:
        pass


class AuthenticateUserWorkflow:
    def authenticate_user(self, login: str, plain_text_password: str) -> UserAuthenticationResult:
        pass


class AuthorizeUserWorkflow:
    def authorize_user_to_access_section(self, login: str, section: AppSection) -> UserAuthorizationResult:
        pass
