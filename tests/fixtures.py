from datetime import date, datetime, time
from decimal import Decimal
from sqlalchemy.orm import Session
from zwpa.model import (
    ClientRequest,
    Location,
    Product,
    TimeWindow,
    Transport,
    TransportRequest,
    UserRole,
    Warehouse,
)
from zwpa.model import UserRoleAssignment

from zwpa.model import User
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import TodayProvider
from zwpa.workflows.client_requests.GetClientRequestsWorkflow import ClientRequestView
from zwpa.workflows.transport.ListTransportRequestsWorkflow import TransportRequestView
from zwpa.workflows.user.ListUserRolesWorkflow import UserRolesView


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
    def new_transporter(
        cls,
        session: Session,
        id: int | None = None,
        login: str = "user",
        password: bytes = b"password",
        login_attempts_left: int = 3,
    ) -> User:
        if id is None:
            id = cls.next_id()

        user = cls.new_user(session, id=id)
        cls.new_role_assignment(session, user_id=id, role=UserRole.TRANSPORT)
        return user

    @classmethod
    def new_role_assignment(
        cls,
        session: Session,
        role: UserRole,
        user_id: int,
        id: int | None = None,
    ) -> UserRoleAssignment:
        user_role_assignment = UserRoleAssignment(
            role=role, user_id=user_id, id=id if id is not None else cls.next_id()
        )
        session.add(user_role_assignment)
        return user_role_assignment

    @classmethod
    def new_product(
        cls,
        session: Session,
        id: int | None = None,
        label: str = "BOXES",
        unit: str = "ISO_CONTAINER",
    ) -> Product:
        product = Product(
            id=id if id is not None else cls.next_id(), label=label, unit=unit
        )
        session.add(product)
        return product

    @classmethod
    def new_time_window(
        cls,
        session: Session,
        id: int | None = None,
        start: time = time(6, 0),
        end: time = time(15, 0),
    ) -> TimeWindow:
        time_window = TimeWindow(
            id=id if id is not None else cls.next_id(), start=start, end=end
        )
        session.add(time_window)
        return time_window

    @classmethod
    def new_location(
        cls,
        session: Session,
        id: int | None = None,
        longitude: float = 12.33,
        latitude: float = 8.55,
    ) -> Location:
        location = Location(
            id=id if id is not None else cls.next_id(),
            longitude=longitude,
            latitude=latitude,
        )
        session.add(location)
        return location

    @classmethod
    def new_client_request(
        cls,
        session: Session,
        product_id: int | None = None,
        client_id: int | None = None,
        supply_time_window_id: int | None = None,
        destination_id: int | None = None,
        price: Decimal = Decimal("0.99"),
        unit_count: int = 1,
        request_deadline: date = date(2020, 1, 1),
        transport_deadline: date = date(2020, 2, 1),
        accepted: bool = False,
        id: int | None = None,
    ) -> ClientRequest:
        if product_id is None:
            product_id = cls.next_id()
            cls.new_product(session, id=product_id)
        if client_id is None:
            client_id = cls.next_id()
            cls.new_user(session, id=client_id)
        if supply_time_window_id is None:
            supply_time_window_id = cls.next_id()
            cls.new_time_window(session, id=supply_time_window_id)
        if destination_id is None:
            destination_id = cls.next_id()
            cls.new_location(session, id=destination_id)
        client_request = ClientRequest(
            product_id=product_id,
            client_id=client_id,
            supply_time_window_id=supply_time_window_id,
            destination_id=destination_id,
            id=id if id is not None else cls.next_id(),
            price=price,
            unit_count=unit_count,
            request_deadline=request_deadline,
            transport_deadline=transport_deadline,
            accepted=accepted,
        )
        session.add(client_request)
        return client_request

    @classmethod
    def new_client_request_view(
        cls,
        client_id: int,
        id: int | None = None,
        product_name: str = "BOXES",
        product_unit: str = "ISO_CONTAINER",
        destination_longitude: float = 12.33,
        destination_latitude: float = 8.55,
        supply_time_window_start: time = time(6, 0),
        supply_time_window_end: time = time(15, 0),
        price: Decimal = Decimal("0.99"),
        unit_count: int = 1,
        request_deadline: date = date(2020, 1, 1),
        transport_deadline: date = date(2020, 2, 1),
        accepted: bool = False,
    ) -> ClientRequestView:
        return ClientRequestView(
            id=id if id is not None else cls.next_id(),
            client_id=client_id,
            product_name=product_name,
            product_unit=product_unit,
            price=price,
            unit_count=unit_count,
            request_deadline=request_deadline,
            transport_deadline=transport_deadline,
            destination_longitude=destination_longitude,
            destination_latitude=destination_latitude,
            supply_time_window_start=supply_time_window_start,
            supply_time_window_end=supply_time_window_end,
            accepted=accepted,
        )

    @classmethod
    def new_warehouse(
        cls,
        session: Session,
        location_id: int | None = None,
        label: str = "Test Warehouse",
        id: int | None = None,
    ) -> Warehouse:
        if location_id is None:
            location_id = cls.next_id()
            cls.new_location(session, id=location_id)

        warehouse = Warehouse(
            id=id if id is not None else cls.next_id(),
            location_id=location_id,
            label=label,
        )
        session.add(warehouse)
        return warehouse

    @classmethod
    def new_today_provider(
        cls, today: datetime = datetime(2020, 1, 1)
    ) -> TodayProvider:
        class FakeTodayProvider:
            def today(self) -> datetime:
                return today

        return FakeTodayProvider()

    @classmethod
    def new_user_roles_view(
        cls,
        user_id: int,
        user_login: str = "user",
        is_admin: bool = False,
        is_clerk: bool = False,
        is_client: bool = False,
        is_supplier: bool = False,
        is_transport: bool = False,
    ) -> UserRolesView:
        return UserRolesView(
            id=user_id,
            login=user_login,
            is_admin=is_admin,
            is_clerk=is_clerk,
            is_client=is_client,
            is_supplier=is_supplier,
            is_transport=is_transport,
        )

    @classmethod
    def new_transport(
        cls,
        session: Session,
        unit_count: int = 1,
        price: Decimal = Decimal(1.0),
        pickup_location_id: int | None = None,
        destination_location_id: int | None = None,
        load_time_window_id: int | None = None,
        destination_time_window_id: int | None = None,
        id: int | None = None,
    ) -> Transport:
        if pickup_location_id is None:
            pickup_location_id = cls.new_location(session).id

        if destination_location_id is None:
            destination_location_id = cls.new_location(session).id

        if load_time_window_id is None:
            load_time_window_id = cls.new_time_window(session).id

        if destination_time_window_id is None:
            destination_time_window_id = cls.new_time_window(session).id

        transport = Transport(
            id=id if id is not None else cls.next_id(),
            unit_count=unit_count,
            price=price,
            pickup_location_id=pickup_location_id,
            destination_location_id=destination_location_id,
            load_time_window_id=load_time_window_id,
            destination_time_window_id=destination_time_window_id,
        )
        session.add(transport)
        return transport

    @classmethod
    def new_transport_request(
        cls,
        session: Session,
        transport_id: int,
        request_deadline: date = date(2020, 1, 1),
        accepted: bool = False,
        id: int | None = None,
    ) -> TransportRequest:
        transport_request = TransportRequest(
            transport_id=transport_id,
            id=id if id is not None else cls.next_id(),
            request_deadline=request_deadline,
            accepted=accepted,
        )
        session.add(transport_request)
        return transport_request

    @classmethod
    def new_transport_request_view(
        cls,
        request_id: int,
        unit_count: int = 1,
        price: Decimal = Decimal(1.0),
        pickup_location_longitude: float = 12.33,
        pickup_location_latitude: float = 8.55,
        destination_location_longitude: float = 12.33,
        destination_location_latitude: float = 8.55,
        load_time_window_start: time = time(6, 0),
        load_time_window_end: time = time(15, 0),
        destination_time_window_start: time = time(6, 0),
        destination_time_window_end: time = time(15, 0),
        request_deadline: date = date(2020, 1, 1),
    ) -> TransportRequestView:
        return TransportRequestView(
            request_id=request_id,
            unit_count=unit_count,
            price=price,
            pickup_location_longitude=pickup_location_longitude,
            pickup_location_latitude=pickup_location_latitude,
            destination_location_longitude=destination_location_longitude,
            destination_location_latitude=destination_location_latitude,
            load_time_window_start=load_time_window_start,
            load_time_window_end=load_time_window_end,
            destination_time_window_start=destination_time_window_start,
            destination_time_window_end=destination_time_window_end,
            request_deadline=request_deadline,
        )
