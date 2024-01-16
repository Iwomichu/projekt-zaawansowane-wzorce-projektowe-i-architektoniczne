from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import Product, WarehouseProduct
from zwpa.workflows.retail.CartManager import CartManager
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class InitializeCartManagerWorkflow:
    def __init__(self, session_maker: sessionmaker[Session], cart_manager: CartManager) -> None:
        self.cart_manager = cart_manager
        self.session_maker = session_maker

    def initialize_cart_manager(self) -> None:
        with self.session_maker() as session:
            query = (
                select(
                    Product.id.label("product_id"),
                    func.coalesce(func.count(WarehouseProduct.id), 0).label(
                        "available_count"
                    ),
                )
                .join(WarehouseProduct, isouter=True)
                .group_by(Product.id)
            )
            self.cart_manager.initialize(
                available_count_by_product_id={
                    product_id: available_count
                    for product_id, available_count in session.execute(query).all()
                }
            )
