from datetime import date, time
from decimal import Decimal
from sqlalchemy.orm import Session
from zwpa.model import ClientRequest, Location, Product, TimeWindow, UserRole
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
        label: str = "BOXES",
        unit: str = "ISO_CONTAINER",
    ) -> Product:
        product = Product(label=label, unit=unit)
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
        product_id: int,
        client_id: int,
        supply_time_window_id: int,
        destination_id: int,
        price: Decimal = Decimal("0.99"),
        unit_count: int = 1,
        request_deadline: date = date(2020, 1, 1),
        transport_deadline: date = date(2020, 2, 1),
        id: int | None = None,
    ) -> ClientRequest:
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
        )
        session.add(client_request)
        return client_request
