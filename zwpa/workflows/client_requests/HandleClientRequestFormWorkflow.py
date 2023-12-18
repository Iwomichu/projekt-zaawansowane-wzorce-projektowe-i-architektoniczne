from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from zwpa.model import Product, UserRole

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


@dataclass
class ProductView:
    id: int
    label: str

    @staticmethod
    def from_product(product: Product) -> ProductView:
        return ProductView(id=product.id, label=product.label)


class HandleClientRequestFormWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(session_maker)

    def get_client_request_form_init_data(self, user_id: int) -> list[ProductView]:
        self.user_role_checker.assert_user_of_role(user_id, UserRole.CLIENT)
        with self.session_maker() as session:
            products = session.execute(select(Product)).scalars()
            return [
                ProductView(id=product.id, label=product.label) for product in products
            ]
