from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from zwpa.model import TransportOffer, TransportOfferStatus, TransportStatus, UserRole
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import (
    DefaultTodayProvider,
    TodayProvider,
)

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class AcceptTransportOfferForRequestWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker[Session],
        today_provider: TodayProvider = DefaultTodayProvider(),
    ) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)
        self.today_provider = today_provider

    def accept_transport_offer_for_request(
        self, user_id: int, transport_offer_id: int, transport_request_id: int
    ) -> None:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        with self.session_maker() as session:
            transport_offer = session.get_one(TransportOffer, transport_offer_id)
            transport_offer.status = TransportOfferStatus.ACCEPTED
            other_transport_offers = session.execute(
                select(TransportOffer)
                .where(TransportOffer.transport_id == transport_offer.transport_id)
                .where(TransportOffer.id != transport_offer_id)
            ).scalars()
            for other_transport_offer in other_transport_offers:
                other_transport_offer.status = TransportOfferStatus.REJECTED
            transport_offer.transport.status = TransportStatus.OFFER_ACCEPTED
            session.commit()
