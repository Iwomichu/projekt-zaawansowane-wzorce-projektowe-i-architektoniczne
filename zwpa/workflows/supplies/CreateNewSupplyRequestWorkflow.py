from datetime import date
from sqlalchemy.orm import Session, sessionmaker
from zwpa.model import Supply, SupplyRequest, SupplyStatus, UserRole

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class CreateNewSupplyRequestWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def create_new_supply_request(self, user_id: int, warehouse_id: int, product_id: int, time_window_id: int, unit_count: int, request_deadline: date) -> None:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        with self.session_maker() as session:
            supply = Supply(
                unit_count=unit_count,
                status=SupplyStatus.REQUESTED,
                product_id=product_id,
                warehouse_id=warehouse_id,
                supply_time_window_id=time_window_id,
            )
            session.add(supply)
            supply_request = SupplyRequest(
                request_deadline=request_deadline,
                supply=supply,
                clerk_id=user_id,
            )
            session.add(supply_request)
            session.commit()
