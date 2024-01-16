
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel


class Cart(BaseModel):
    user_id: int
    amount_by_product_id: dict[int, int]


class NotEnoughProductCountAvailableException(Exception):
    pass

class ProductNotFoundException(Exception):
    pass


class CartManager(ABC):
    @abstractmethod
    def initialize(self, available_count_by_product_id: dict[int, int]) -> None:
        pass

    @abstractmethod
    def put_in_cart(self, product_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    def remove_from_cart(self, product_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    def get_cart(self, user_id: int) -> Cart:
        pass

    @abstractmethod
    def checkout(self, user_id: int) -> None:
        pass

    @abstractmethod
    def reduce_available_count(self, product_id: int, amount: int) -> None:
        pass

    @abstractmethod
    def increase_available_count(self, product_id: int, amount: int) -> None:
        pass
