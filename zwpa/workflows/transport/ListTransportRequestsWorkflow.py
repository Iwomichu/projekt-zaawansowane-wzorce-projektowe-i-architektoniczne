from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException

from zwpa.model import TransportRequest, TransportStatus, User, UserRole, Transport
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import (
    DefaultTodayProvider,
    TodayProvider,
)


@dataclass
class TransportRequestView:
    request_id: int
    unit_count: int
    price: Decimal
    pickup_location_longitude: float
    pickup_location_latitude: float
    destination_location_longitude: float
    destination_location_latitude: float
    load_time_window_start: time
    load_time_window_end: time
    destination_time_window_start: time
    destination_time_window_end: time
    request_deadline: date


class ListTransportRequestsWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker,
        today_provider: TodayProvider = DefaultTodayProvider(),
    ) -> None:
        self.session_maker = session_maker
        self.today_provider = today_provider

    def list_available_transport_requests(
        self, user_id: int
    ) -> list[TransportRequestView]:
        with self.session_maker() as session:
            if not self.__is_user_of_role(
                session, user_id=user_id, role=UserRole.TRANSPORT
            ):
                raise UserLacksRoleException()

            requests = self.__get_all_available_requests(session)
            return [
                self.__create_transport_request_view(request) for request in requests
            ]

    def __is_user_of_role(self, session: Session, user_id: int, role: UserRole) -> bool:
        user_roles = [
            assignment.role for assignment in session.get_one(User, user_id).roles
        ]
        return role in user_roles

    def __create_transport_request_view(
        self, transport_request: TransportRequest
    ) -> TransportRequestView:
        transport = transport_request.transport
        return TransportRequestView(
            request_id=transport_request.id,
            unit_count=transport.unit_count,
            price=transport.price,
            pickup_location_longitude=transport.pickup_location.longitude,
            pickup_location_latitude=transport.pickup_location.latitude,
            destination_location_longitude=transport.destination_location.longitude,
            destination_location_latitude=transport.destination_location.latitude,
            load_time_window_start=transport.load_time_window.start,
            load_time_window_end=transport.load_time_window.end,
            destination_time_window_start=transport.destination_time_window.start,
            destination_time_window_end=transport.destination_time_window.end,
            request_deadline=transport_request.request_deadline,
        )

    def __get_all_available_requests(self, session: Session) -> list[TransportRequest]:
        return list(
            session.execute(
                select(TransportRequest)
                .where(
                    TransportRequest.request_deadline
                    < self.today_provider.today().date()
                )
                .where(TransportRequest.transport.has(status=TransportStatus.REQUESTED))
            ).scalars()
        )
