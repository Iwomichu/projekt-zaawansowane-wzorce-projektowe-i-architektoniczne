from dataclasses import dataclass
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import UserRole, Warehouse

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


@dataclass
class WarehouseView:
    id: int
    label: str
    longitude: float
    latitude: float

    @staticmethod
    def create(warehouse: Warehouse):
        return WarehouseView(
            id=warehouse.id,
            label=warehouse.label,
            longitude=warehouse.location.longitude,
            latitude=warehouse.location.latitude,
        )


class ListAllWarehousesWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def list_all_warehouses(self, user_id: int) -> list[WarehouseView]:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        with self.session_maker() as session:
            return [
                WarehouseView.create(warehouse)
                for warehouse in session.query(Warehouse)
            ]
