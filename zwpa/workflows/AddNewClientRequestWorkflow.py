from abc import abstractmethod
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Protocol
from sqlalchemy.orm import sessionmaker

from zwpa.model import ClientRequest, Location, Product, TimeWindow, User, UserRole


class ClientRequestValidationException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class UserIsNotAClient(Exception):
    pass


class TodayProvider(Protocol):
    @abstractmethod
    def today(self) -> datetime:
        pass


class DefaultTodayProvider:
    def today(self) -> datetime:
        return datetime.today().astimezone(timezone.utc)


class AddNewClientRequestWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker,
        min_days_to_process: int,
        today_provider: TodayProvider = DefaultTodayProvider(),
    ) -> None:
        self.session_maker = session_maker
        self.min_days_to_process = min_days_to_process
        self.today_provider = today_provider

    def add_new_client_request(
        self,
        user_id: int,
        price: Decimal,
        unit_count: int,
        request_deadline: date,
        transport_deadline: date,
        product_id: int,
        supply_time_window: tuple[time, time],
        destination: tuple[float, float],
    ) -> None:
        if not self._user_is_client(user_id):
            raise UserIsNotAClient()

        self._validate_user_input(
            price=price,
            unit_count=unit_count,
            request_deadline=request_deadline,
            transport_deadline=transport_deadline,
            product_id=product_id,
            supply_time_window=supply_time_window,
        )

        with self.session_maker() as session:
            time_window = TimeWindow(start=supply_time_window[0], end=supply_time_window[1])
            location = Location(longitude = destination[0], latitude =destination[1])
            session.add(time_window)
            session.add(location)
            session.commit()

            client_request = ClientRequest(
                client_id=user_id,
                price=price,
                unit_count=unit_count,
                request_deadline=request_deadline,
                transport_deadline=transport_deadline,
                product_id=product_id,
                supply_time_window_id=time_window.id,
                destination_id=location.id,
            )
            session.add(client_request)
            session.commit()

    def _user_is_client(self, user_id: int) -> bool:
        with self.session_maker() as session:
            user_roles = [
                assignment.role for assignment in session.get_one(User, user_id).roles
            ]
            return UserRole.CLIENT in user_roles

    def _validate_user_input(
        self,
        price: Decimal,
        unit_count: int,
        request_deadline: date,
        transport_deadline: date,
        product_id: int,
        supply_time_window: tuple[time, time],
    ) -> None:
        if price <= 0:
            raise ClientRequestValidationException(
                f"Price should be positive, but is {price}"
            )
        if datetime.combine(
            request_deadline, time(0, 0), tzinfo=timezone.utc
        ) > self.today_provider.today() + timedelta(days=self.min_days_to_process):
            raise ClientRequestValidationException(
                f"Request deadline too soon. Should be at least {self.min_days_to_process} from today"
            )
        if transport_deadline < request_deadline:
            raise ClientRequestValidationException(
                "Transport deadline should be greater or equal to request deadline"
            )
        if unit_count <= 0:
            raise ClientRequestValidationException(
                f"Unit count should be greater than 0, but is {unit_count}"
            )
        window_start, window_end = supply_time_window
        if window_end.hour < window_start.hour + 1:
            raise ClientRequestValidationException(
                "Supply window should be at least 1 hour"
            )
        with self.session_maker.begin() as session:
            product = session.get(Product, product_id)

            if product is None:
                raise ClientRequestValidationException(
                    f"Unknown product id={product_id}"
                )
