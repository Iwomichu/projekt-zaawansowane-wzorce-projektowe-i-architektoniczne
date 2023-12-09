from datetime import date
import decimal
from enum import Enum
import re
from zwpa.types import McfHash
from sqlalchemy import (
    Boolean,
    Date,
    Dialect,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
    TypeDecorator,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as pgEnum, MONEY
from typing import Any, List, Optional


metadata = MetaData()


class Base(DeclarativeBase):
    metadata = metadata


LOGIN_ATTEMPTS = 3


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String, index=True)
    password: Mapped[McfHash] = mapped_column(LargeBinary)
    login_attempts_left: Mapped[int] = mapped_column(Integer)
    permissions: Mapped[List["UserSectionPermissionRecord"]] = relationship(
        back_populates="user"
    )
    roles: Mapped[List["UserRoleAssignment"]] = relationship(back_populates="user")


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


class NumericMoney(TypeDecorator):
    impl = MONEY

    def process_result_value(
        self, value: Any, dialect: Dialect
    ) -> Optional[decimal.Decimal]:
        if value is not None:
            # adjust this for the currency and numeric
            m = re.match(r"\$([\d.]+)", value)
            if m:
                value = decimal.Decimal(m.group(1))
        return value


class ClientRequest(Base):
    __tablename__ = "client_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    deadline: Mapped[date] = mapped_column(Date)
    price: Mapped[NumericMoney] = mapped_column(NumericMoney)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String)


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


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CLERK = "CLERK"
    CLIENT = "CLIENT"
    SUPPLIER = "SUPPLIER"
    TRANSPORT = "TRANSPORT"


UserRoleType: pgEnum = pgEnum(
    UserRole,
    name="user_role",
    create_constraint=True,
    metadata=Base.metadata,
    validate_strings=True,
)


class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    role = mapped_column(UserRoleType)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="roles")


class UserSectionPermissionRecord(Base):
    __tablename__ = "user_section_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="permissions")
    section = mapped_column(AppSectionType)
