from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from dataclasses import dataclass
from zwpa.model import TransportOffer, TransportRequest, UserRole
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import TodayProvider
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


@dataclass
class TransportOfferView:
    transport_offer_id: int
    transporter_id: int
    transporter_login: str


class ListTransportOffersForRequestWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker[Session],
    ) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def list_transport_offer_for_request(
        self, user_id: int, transport_request_id: int
    ) -> list[TransportOfferView]:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        with self.session_maker() as session:
            transport_request = session.execute(
                select(TransportRequest).where(
                    TransportRequest.id == transport_request_id
                )
            ).scalar_one()
            transport_offers = session.execute(
                select(TransportOffer).where(
                    TransportOffer.transport_id == transport_request.transport_id
                )
            ).scalars()
            return [
                TransportOfferView(
                    transport_offer_id=transport_offer.id,
                    transporter_id=transport_offer.transporter_id,
                    transporter_login=transport_offer.transporter.login,
                )
                for transport_offer in transport_offers
            ]
