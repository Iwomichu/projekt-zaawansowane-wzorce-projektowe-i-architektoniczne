from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import Transport, TransportStatus, UserRole
from zwpa.workflows.transport.TransportAccessChecker import TransportAccessChecker

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class ChangeTransportStatusWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.transport_access_checker = TransportAccessChecker(self.session_maker)

    def change_transport_status(
        self, user_id: int, transport_id: int, new_status: TransportStatus
    ) -> None:
        assert self.transport_access_checker.is_transporter_of_this_transport(
            user_id, transport_id
        )
        with self.session_maker() as session:
            session.get_one(Transport, transport_id).status = new_status
            session.commit()
