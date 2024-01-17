from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import Transport, TransportStatus
from zwpa.workflows.retail.HandleArrivingRetailPackageWorkflow import (
    HandleArrivingRetailPackageWorkflow,
)
from zwpa.workflows.supplies.HandleArrivingSupplyWorkflow import (
    HandleArrivingSupplyWorkflow,
)
from zwpa.workflows.transport.TransportAccessChecker import TransportAccessChecker


class ChangeTransportStatusWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.transport_access_checker = TransportAccessChecker(self.session_maker)
        self.handle_arriving_supply_workflow = HandleArrivingSupplyWorkflow(
            session_maker
        )
        self.handle_arriving_retail_package_workflow = (
            HandleArrivingRetailPackageWorkflow(session_maker)
        )

    def change_transport_status(
        self, user_id: int, transport_id: int, new_status: TransportStatus
    ) -> None:
        assert self.transport_access_checker.is_transporter_of_this_transport(
            user_id, transport_id
        )
        with self.session_maker() as session:
            session.get_one(Transport, transport_id).status = new_status
            if new_status is TransportStatus.COMPLETE:
                self.handle_arriving_supply_workflow.handle_arrival_if_transport_was_supply(
                    transport_id
                )
                self.handle_arriving_retail_package_workflow.handle_arrival_if_transport_was_retail(
                    transport_id
                )
            session.commit()
