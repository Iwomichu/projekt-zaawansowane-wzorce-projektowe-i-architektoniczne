from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import SupplyRequest, UserRole

from zwpa.views.SupplyRequestView import SupplyRequestView
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


@dataclass(eq=True)
class SupplyOfferFormInitData:
    supply_request: SupplyRequestView


class HandleSupplyOfferFormWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def get_form_data(
        self, user_id: int, supply_request_id: int
    ) -> SupplyOfferFormInitData:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.SUPPLIER)
        with self.session_maker() as session:
            supply_request = (
                session.query(SupplyRequest)
                .where(SupplyRequest.id == supply_request_id)
                .one()
            )
            return SupplyOfferFormInitData(
                supply_request=SupplyRequestView.from_supply_request(supply_request)
            )
