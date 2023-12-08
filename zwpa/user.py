from dataclasses import dataclass
from enum import Enum
from typing import List, NewType, Optional
import bcrypt
from sqlalchemy import Boolean, ForeignKey, Integer, MetaData, String, LargeBinary, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker, relationship
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
    USER_MANAGEMENT = "USER_MANAGEMENT"


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
    permissions: Mapped[List["UserSectionPermissionRecord"]] = relationship(back_populates="user")


class UserSectionPermissionRecord(Base):
    __tablename__ = "user_section_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="permissions")
    section = mapped_column(AppSectionType)


class UserAuthenticationLogRecord(Base):
    __tablename__ = "user_authentication_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String, index=True)
    authenticated: Mapped[bool] = mapped_column(Boolean)


class UserAuthorizationLogRecord:
    __tablename__ = "user_authorization_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String, index=True)
    authorized: Mapped[bool] = mapped_column(Boolean)
    section = mapped_column(AppSectionType)


@dataclass
class UserAuthenticationResult:
    authenticated: bool


@dataclass
class UserAuthorizationResult:
    authorized: bool


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
    def __init__(self, user_login: str, authentication_result: UserAuthenticationLogRecord) -> None:
        self.authentication_result = authentication_result
        super().__init__(f"User '{user_login=}' has no logging attempts left")


class CreateUserWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    def create_user(self, login: str, plain_text_password: str) -> None:
        with self.session_maker() as session:
            if self._user_exists(session, login=login):
                raise UserAlreadyExistsException(login)
            
            session.add(User(
                login=login, 
                password=self._hash_password(plain_text_password), 
                login_attempts_left=LOGIN_ATTEMPTS
            ))
            session.commit()
            
    def _user_exists(self, session: Session, login: str) -> bool:
        return session.scalars(select(User).filter_by(login=login)).first() is not None
    
    def _hash_password(self, plain_text_password: str) -> McfHash:
        return McfHash(bcrypt.hashpw(plain_text_password.encode(encoding="utf-8"), salt=bcrypt.gensalt()))


class AuthenticateUserWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    def authenticate_user(self, login: str, plain_text_password: str) -> UserAuthenticationLogRecord:
        authenticated = False
        try:
            with self.session_maker() as session:
                user = self._get_user(session, login=login)

                if user is None:
                    raise UserDoesNotExist(user_login=login)

                if user.login_attempts_left < 1:
                    raise UserHasNoLoginAttemptsLeft(user_login=user, authentication_result=UserAuthenticationResult(authenticated=False))
                
                if not self._passwords_match(plain_text_password=plain_text_password, hashed_password=user.password):
                    user.login_attempts_left -= 1
                    session.commit()
                    raise UserHasDifferentPassword(user_login=user, authentication_result=UserAuthenticationResult(authenticated=False))
                
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


class AuthorizeUserWorkflow:
    def authorize_user_to_access_section(self, login: str, section: AppSection) -> UserAuthorizationLogRecord:
        pass
