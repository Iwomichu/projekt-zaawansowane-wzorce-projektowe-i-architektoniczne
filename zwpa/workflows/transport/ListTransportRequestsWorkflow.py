from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException

from zwpa.model import (
    SupplyOffer,
    TransportOffer,
    TransportRequest,
    TransportStatus,
    User,
    UserRole,
    Transport,
)
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import (
    DefaultTodayProvider,
    TodayProvider,
)
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


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
    user_already_made_offer_on_the_request: bool


class ListTransportRequestsWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker,
        today_provider: TodayProvider = DefaultTodayProvider(),
    ) -> None:
        self.session_maker = session_maker
        self.today_provider = today_provider
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def list_available_transport_requests(
        self, user_id: int
    ) -> list[TransportRequestView]:
        with self.session_maker() as session:
            self.user_role_checker.assert_user_with_one_of_roles(
                user_id, roles=[UserRole.TRANSPORT, UserRole.CLERK]
            )

            requests = self.__get_all_available_requests(session)
            user_transport_offers = self.__get_all_transport_offers_by_the_user(
                session, user_id
            )
            already_offered_transports = {
                user_transport_offer.transport_id
                for user_transport_offer in user_transport_offers
            }
            return [
                self.__create_transport_request_view(
                    request, already_offered_transports
                )
                for request in requests
            ]

    def __create_transport_request_view(
        self,
        transport_request: TransportRequest,
        already_offered_transport_ids: set[int],
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
            user_already_made_offer_on_the_request=transport_request.transport.id
            in already_offered_transport_ids,
        )

    def __get_all_available_requests(self, session: Session) -> list[TransportRequest]:
        return list(
            session.execute(
                select(TransportRequest)
                .where(
                    TransportRequest.request_deadline
                    > self.today_provider.today().date()
                )
                .where(TransportRequest.transport.has(status=TransportStatus.REQUESTED))
            ).scalars()
        )

    def __get_all_transport_offers_by_the_user(
        self, session: Session, user_id: int
    ) -> list[TransportOffer]:
        return list(
            session.execute(
                select(TransportOffer).where(TransportOffer.transporter_id == user_id)
            ).scalars()
        )
