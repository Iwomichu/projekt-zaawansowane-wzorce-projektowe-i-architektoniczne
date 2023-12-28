from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import SupplyRequest, SupplyStatus, UserRole
from zwpa.views.SupplyRequestView import SupplyRequestView
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class ListSupplyRequestsWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def list_supply_requests(self, user_id: int) -> list[SupplyRequestView]:
        self.user_role_checker.assert_user_with_one_of_roles(
            user_id, roles=[UserRole.CLERK, UserRole.SUPPLIER]
        )

        with self.session_maker() as session:
            supply_requests = session.query(SupplyRequest).all()
            return [
                SupplyRequestView.from_supply_request(supply_request)
                for supply_request in supply_requests
                if supply_request.supply.status is SupplyStatus.REQUESTED
            ]
