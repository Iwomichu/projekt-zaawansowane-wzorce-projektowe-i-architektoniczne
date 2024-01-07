from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import (
    Transport,
    TransportOffer,
    TransportOfferStatus,
)
from zwpa.workflows.transport.ListTransportsWorkflow import CompleteTransportView
from zwpa.workflows.transport.TransportAccessChecker import TransportAccessChecker


class GetTransportWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.transport_access_checker = TransportAccessChecker(self.session_maker)

    def get_transport(self, user_id: int, transport_id: int) -> CompleteTransportView:
        self.transport_access_checker.assert_user_has_access_to_transport(user_id, transport_id)
        with self.session_maker() as session:
            transport = session.get_one(Transport, transport_id)
            accepted_offer = (
                session.query(TransportOffer)
                .where(TransportOffer.transport_id == transport_id)
                .where(TransportOffer.status == TransportOfferStatus.ACCEPTED)
                .one_or_none()
            )
            return CompleteTransportView.create(transport, accepted_offer)
