from decimal import Decimal
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import Product, UserRole
from zwpa.workflows.product.ListProductsWorkflow import (
    FullProductView,
    build_full_product_view_query,
)

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class HandleProductDetailsWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def get_product_details(self, user_id: int, product_id: int) -> FullProductView:
        self._assert_access(user_id)
        query = build_full_product_view_query()
        with self.session_maker() as session:
            result = session.execute(query.where(Product.id == product_id)).fetchone()
            if result is None:
                raise RuntimeError()
            return FullProductView(
                *result
            )

    def modify_product_details(
        self, user_id: int, product_id: int, label: str, retail_price: Decimal
    ) -> None:
        self._assert_access(user_id)
        with self.session_maker() as session:
            product = session.get_one(Product, product_id)
            product.label = label
            product.retail_price = retail_price
            session.commit()

    def _assert_access(self, user_id: int) -> None:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
