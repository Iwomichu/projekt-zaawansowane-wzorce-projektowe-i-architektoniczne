from datetime import date, datetime, time
import decimal
from enum import Enum
import re
from zwpa.types import McfHash
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Dialect,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    Time,
    TypeDecorator,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as pgEnum, MONEY
from typing import Any, List, Optional


metadata = MetaData()


class Base(DeclarativeBase):
    metadata = metadata


LOGIN_ATTEMPTS = 3


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)


class TimeWindow(Base):
    __tablename__ = "time_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    start: Mapped[time] = mapped_column(Time)
    end: Mapped[time] = mapped_column(Time)


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
    price: Mapped[decimal.Decimal] = mapped_column(NumericMoney)
    unit_count: Mapped[int] = mapped_column(Integer)
    request_deadline: Mapped[date] = mapped_column(Date)
    transport_deadline: Mapped[date] = mapped_column(Date)
    accepted: Mapped[bool] = mapped_column(Boolean)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    supply_time_window_id: Mapped[int] = mapped_column(ForeignKey("time_windows.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)

    product: Mapped["Product"] = relationship(foreign_keys=[product_id])
    client: Mapped["User"] = relationship(foreign_keys=[client_id])
    destination: Mapped["Location"] = relationship(foreign_keys=[destination_id])
    supply_time_window: Mapped["TimeWindow"] = relationship(
        foreign_keys=[supply_time_window_id]
    )


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


class Transport(Base):
    __tablename__ = "transports"

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_count: Mapped[int] = mapped_column(Integer)
    price: Mapped[decimal.Decimal] = mapped_column(NumericMoney)

    pickup_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    destination_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    load_time_window_id: Mapped[int] = mapped_column(ForeignKey("time_windows.id"))
    destination_time_window_id: Mapped[int] = mapped_column(
        ForeignKey("time_windows.id")
    )

    pickup_location: Mapped["Location"] = relationship(
        foreign_keys=[pickup_location_id]
    )
    destination_location: Mapped["Location"] = relationship(
        foreign_keys=[destination_location_id]
    )
    load_time_window: Mapped["TimeWindow"] = relationship(
        foreign_keys=[load_time_window_id]
    )
    destination_time_window: Mapped["TimeWindow"] = relationship(
        foreign_keys=[destination_time_window_id]
    )


class TransportRequest(Base):
    __tablename__ = "transport_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_deadline: Mapped[date] = mapped_column(Date)
    accepted: Mapped[bool] = mapped_column(Boolean)
    transport_id: Mapped[int] = mapped_column(ForeignKey("transports.id"))

    transport: Mapped["Transport"] = relationship()


warehouse_time_windows_associate_table = Table(
    "warehouse_time_windows_associate_table",
    Base.metadata,
    Column("warehouse_id", ForeignKey("warehouses.id"), primary_key=True),
    Column("time_window_id", ForeignKey("time_windows.id"), primary_key=True),
)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String, nullable=False)

    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    location: Mapped["Location"] = relationship()
    load_time_windows: Mapped[list["TimeWindow"]] = relationship(
        secondary=warehouse_time_windows_associate_table
    )


class SupplyStatus(str, Enum):
    OFFERED_WITHOUT_REQUEST = "OFFERED_WITHOUT_REQUEST"
    REQUESTED = "REQUESTED"
    OFFER_ACCEPTED = "OFFER_ACCEPTED"
    COMPLETE = "COMPLETE"


SupplyStatusType: pgEnum = pgEnum(
    SupplyStatus,
    name="supply_status",
    create_constraint=True,
    metadata=Base.metadata,
    validate_strings=True,
)


class Supply(Base):
    __tablename__ = "supplies"

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_count: Mapped[int] = mapped_column(Integer)
    status = mapped_column(SupplyStatusType)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    supply_time_window_id: Mapped[int] = mapped_column(
        ForeignKey("time_windows.id"), index=True
    )

    product: Mapped["Product"] = relationship(foreign_keys=[product_id])
    warehouse: Mapped["Warehouse"] = relationship(foreign_keys=[warehouse_id])
    supply_time_window: Mapped["TimeWindow"] = relationship(
        foreign_keys=[supply_time_window_id]
    )
    supply_offers: Mapped[list["SupplyOffer"]] = relationship(back_populates="supply")


class SupplyTransportRequest(Base):
    __tablename__ = "supply_transport_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    supply_id: Mapped[int] = mapped_column(ForeignKey("supplies.id"), index=True)
    transport_request_id: Mapped[int] = mapped_column(
        ForeignKey("transport_requests.id"), index=True
    )

    supply: Mapped["Supply"] = relationship(foreign_keys=[supply_id])
    transport_request: Mapped["TransportRequest"] = relationship(
        foreign_keys=[transport_request_id]
    )


class SupplyReceipt(Base):
    __tablename__ = "supply_receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_acceptance_datetime: Mapped[datetime] = mapped_column(DateTime)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("supply_requests.id"), index=True
    )
    offer_id: Mapped[int] = mapped_column(ForeignKey("supply_offers.id"), index=True)
    clerk_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    request: Mapped["SupplyRequest"] = relationship(foreign_keys=[request_id])
    offer: Mapped["SupplyOffer"] = relationship(foreign_keys=[offer_id])
    clerk: Mapped["User"] = relationship(foreign_keys=[clerk_id])


class SupplyRequest(Base):
    __tablename__ = "supply_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_deadline: Mapped[date] = mapped_column(Date)

    supply_id: Mapped[int] = mapped_column(ForeignKey("supplies.id"), index=True)
    clerk_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    clerk: Mapped["User"] = relationship(foreign_keys=[clerk_id])
    supply: Mapped["Supply"] = relationship(foreign_keys=[supply_id])


class SupplyOffer(Base):
    __tablename__ = "supply_offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[decimal.Decimal] = mapped_column(NumericMoney)
    transport_deadline: Mapped[date] = mapped_column(Date)
    accepted: Mapped[bool] = mapped_column(Boolean)

    supply_id: Mapped[int] = mapped_column(ForeignKey("supplies.id"), index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    load_time_window_id: Mapped[int] = mapped_column(ForeignKey("time_windows.id"))
    source_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), index=True
    )

    supply: Mapped["Supply"] = relationship(foreign_keys=[supply_id])
    supplier: Mapped["User"] = relationship(foreign_keys=[supplier_id])
    source_location: Mapped["Location"] = relationship(
        foreign_keys=[source_location_id]
    )
    load_time_window: Mapped["TimeWindow"] = relationship(
        foreign_keys=[load_time_window_id]
    )
