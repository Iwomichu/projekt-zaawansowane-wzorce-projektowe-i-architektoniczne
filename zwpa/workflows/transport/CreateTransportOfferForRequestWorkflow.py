from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import TransportOffer, TransportRequest, UserRole
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class CreateTransportOfferForRequestWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def create_transport_offer_for_request(self, user_id: int, transport_request_id: int) -> None:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.TRANSPORT)
        with self.session_maker() as session:
            transport_request = session.execute(select(TransportRequest).where(TransportRequest.id == transport_request_id)).scalar_one()
            transport_offer = TransportOffer(transporter_id=user_id, transport_id=transport_request.transport_id)
            session.add(transport_offer)
            session.commit()
    