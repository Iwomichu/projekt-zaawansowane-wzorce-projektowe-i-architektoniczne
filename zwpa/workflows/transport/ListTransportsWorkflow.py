from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session

from zwpa.model import (
    Transport,
    TransportOffer,
    TransportOfferStatus,
    TransportStatus,
    UserRole,
)
from zwpa.views.LocationView import LocationView
from zwpa.workflows.client_requests.HandleClientRequestAcceptanceFormWorkflow import (
    TimeWindowView,
)
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


@dataclass
class CompleteTransportView:
    id: int
    unit_count: int
    price: Decimal
    status: TransportStatus
    pickup_location_longitude: float
    pickup_location_latitude: float
    destination_location_longitude: float
    destination_location_latitude: float
    load_time_window_start: time
    load_time_window_end: time
    destination_time_window_start: time
    destination_time_window_end: time
    transporter_id: int | None
    transporter_login: str | None

    @staticmethod
    def create(transport: Transport, transport_offer: TransportOffer | None):
        return CompleteTransportView(
            id=transport.id,
            unit_count=transport.unit_count,
            price=transport.price,
            status=transport.status,
            pickup_location_longitude=transport.pickup_location.longitude,
            pickup_location_latitude=transport.pickup_location.latitude,
            destination_location_longitude=transport.destination_location.longitude,
            destination_location_latitude=transport.destination_location.latitude,
            load_time_window_start=transport.load_time_window.start,
            load_time_window_end=transport.load_time_window.end,
            destination_time_window_start=transport.destination_time_window.start,
            destination_time_window_end=transport.destination_time_window.end,
            transporter_id=transport_offer.id if transport_offer is not None else None,
            transporter_login=transport_offer.transporter.login
            if transport_offer is not None
            else None,
        )


class ListTransportWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def _list_transports(
        self,
        by_status: list[TransportStatus] | None = None,
        by_transporter: int | None = None,
    ) -> list[CompleteTransportView]:
        with self.session_maker() as session:
            query = select(Transport, TransportOffer).join(TransportOffer, isouter=True)
            if by_status is not None:
                query = query.where(Transport.status.in_(by_status))

            if by_transporter is not None:
                query = query.where(
                    TransportOffer.transporter_id == by_transporter
                ).where(TransportOffer.status == TransportOfferStatus.ACCEPTED)

            items = session.execute(query).fetchall()
            return [
                CompleteTransportView.create(transport, transport_offer)
                for transport, transport_offer in items
            ]

    def list_all_transports(
        self,
        user_id: int,
    ) -> list[CompleteTransportView]:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        return self._list_transports()

    def list_my_transports(self, user_id: int) -> list[CompleteTransportView]:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.TRANSPORT)
        return self._list_transports(by_transporter=user_id)

    def list_transport_with_status(
        self, user_id: int, status: TransportStatus
    ) -> list[CompleteTransportView]:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        return self._list_transports(by_status=[status])
