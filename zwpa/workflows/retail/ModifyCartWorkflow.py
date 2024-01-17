from typing import Callable
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import Product
from zwpa.workflows.retail.CartManager import CartManager
from zwpa.workflows.retail.RetailProductView import PersonalizedRetailProductView
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class ModifyCartWorkflow:
    def __init__(
        self, session_maker: sessionmaker[Session], cart_manager: CartManager
    ) -> None:
        self.session_maker = session_maker
        self.cart_manager = cart_manager

        self.user_role_checker = UserRoleChecker(self.session_maker)

    def put_into_cart(self, user_id: int, product_id: int) -> None:
        self.cart_manager.put_in_cart(product_id=product_id, user_id=user_id)

    def take_from_cart(self, user_id: int, product_id: int) -> None:
        self.cart_manager.remove_from_cart(product_id=product_id, user_id=user_id)
