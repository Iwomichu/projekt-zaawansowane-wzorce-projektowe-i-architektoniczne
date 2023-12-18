from dataclasses import dataclass
from datetime import date
from sqlalchemy.orm import Session, sessionmaker
from zwpa.model import Product, UserRole, Warehouse
from zwpa.workflows.client_requests.HandleClientRequestAcceptanceFormWorkflow import (
    WarehouseView,
)
from zwpa.workflows.client_requests.HandleClientRequestFormWorkflow import ProductView
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


@dataclass(eq=True)
class SupplyRequestFormData:
    warehouses: list[WarehouseView]
    products: list[ProductView]


class HandleSupplyRequestFormWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def get_data(self, user_id: int) -> SupplyRequestFormData:
        self.user_role_checker.assert_user_of_role(user_id, UserRole.CLERK)
        with self.session_maker() as session:
            warehouses = [
                WarehouseView.from_warehouse(warehouse)
                for warehouse in session.query(Warehouse).all()
            ]
            products = [
                ProductView.from_product(product)
                for product in session.query(Product).all()
            ]
            return SupplyRequestFormData(warehouses=warehouses, products=products)
