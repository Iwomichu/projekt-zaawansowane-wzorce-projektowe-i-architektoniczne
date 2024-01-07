from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import (
    ClientRequest,
    ClientTransportRequest,
    Supply,
    SupplyOffer,
    SupplyReceipt,
    SupplyRequest,
    SupplyTransportRequest,
    Transport,
    TransportOffer,
    TransportOfferStatus,
    TransportRequest,
    UserRole,
)
from zwpa.workflows.transport.ListTransportsWorkflow import CompleteTransportView

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class GetTransportWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def get_transport(self, user_id: int, transport_id: int) -> CompleteTransportView:
        self._assert_user_has_access_to_transport(user_id, transport_id)
        with self.session_maker() as session:
            transport = session.get_one(Transport, transport_id)
            accepted_offer = (
                session.query(TransportOffer)
                .where(TransportOffer.transport_id == transport_id)
                .where(TransportOffer.status == TransportOfferStatus.ACCEPTED)
                .one_or_none()
            )
            return CompleteTransportView.create(transport, accepted_offer)

    def _assert_user_has_access_to_transport(
        self, user_id: int, transport_id: int
    ) -> None:
        assert self.is_clerk(user_id) or any(
            functor(user_id, transport_id)
            for functor in (
                self.is_transporter_of_this_transport,
                self.is_receiver_of_this_transport,
                self.is_sender_of_this_transport,
            )
        )

    def is_clerk(self, user_id: int) -> bool:
        return self.user_role_checker.is_user_of_role(user_id, role=UserRole.CLERK)

    def is_transporter_of_this_transport(
        self, user_id: int, transport_id: int
    ) -> bool:
        if not self.user_role_checker.is_user_of_role(user_id, role=UserRole.TRANSPORT):
            return False

        with self.session_maker() as session:
            accepted_transport_offer = (
                session.query(TransportOffer)
                .filter(TransportOffer.transport_id == transport_id)
                .filter(TransportOffer.transporter_id == user_id)
                .filter(TransportOffer.status == TransportOfferStatus.ACCEPTED)
                .one_or_none()
            )
            return accepted_transport_offer is not None

    def is_sender_of_this_transport(self, user_id: int, transport_id: int) -> bool:
        if not self.user_role_checker.is_user_of_role(user_id, role=UserRole.SUPPLIER):
            return False

        with self.session_maker() as session:
            return (
                session.query(SupplyReceipt)
                .join(SupplyRequest, SupplyReceipt.request_id == SupplyRequest.id)
                .join(Supply, SupplyRequest.supply_id == Supply.id)
                .join(
                    SupplyTransportRequest,
                    Supply.id == SupplyTransportRequest.supply_id,
                )
                .join(
                    TransportRequest,
                    SupplyTransportRequest.transport_request_id == TransportRequest.id,
                )
                .where(TransportRequest.transport_id == transport_id)
                .join(SupplyOffer, Supply.id == SupplyOffer.supply_id)
                .where(SupplyOffer.supplier_id == user_id)
                .one_or_none()
                is not None
            )

    def is_receiver_of_this_transport(self, user_id: int, transport_id: int) -> bool:
        if not self.user_role_checker.is_user_of_role(user_id, role=UserRole.CLIENT):
            return False

        with self.session_maker() as session:
            return (
                session.query(TransportRequest)
                .join(
                    ClientTransportRequest,
                    TransportRequest.id == ClientTransportRequest.transport_request_id,
                )
                .join(
                    ClientRequest,
                    ClientTransportRequest.client_request_id == ClientRequest.id,
                )
                .where(ClientRequest.client_id == user_id)
                .where(TransportRequest.transport_id == transport_id)
                .one_or_none()
                is not None
            )
