from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import Product
from zwpa.workflows.retail.CartManager import CartManager
from zwpa.workflows.retail.RetailProductView import PersonalizedRetailProductView
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class GetPersonalizedRetailProductViewsWorkflow:
    def __init__(
        self, session_maker: sessionmaker[Session], cart_manager: CartManager
    ) -> None:
        self.session_maker = session_maker
        self.cart_manager = cart_manager

        self.user_role_checker = UserRoleChecker(self.session_maker)

    def get_personalized_retail_product_views(
        self, user_id: int, query: str = "", only_already_in_cart: bool = False
    ) -> list[PersonalizedRetailProductView]:
        # TODO: Check for permissions
        with self.session_maker() as session:
            user_cart = self.cart_manager.get_cart(user_id)
            sql_query = session.query(Product).where(Product.label.like(f"%{query}%"))
            if only_already_in_cart:
                sql_query = sql_query.where(
                    Product.id.in_(user_cart.amount_by_product_id.keys())
                )
            products = sql_query.all()
            current_product_counts = self.cart_manager.get_current_product_counts()
            return [
                PersonalizedRetailProductView(
                    id=product.id,
                    label=product.label,
                    price=product.retail_price,
                    unit=product.unit,
                    already_in_cart=user_cart.amount_by_product_id.get(product.id, 0),
                    available=current_product_counts[product.id],
                )
                for product in products
            ]
