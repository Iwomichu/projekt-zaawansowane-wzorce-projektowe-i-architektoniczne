from dataclasses import asdict
from datetime import datetime
from pydantic import BaseModel
import requests
from zwpa.workflows.retail.CartManager import Cart, CartManager


class RestCartEntry(BaseModel):
    unit_count: int = 0


class RestCart(BaseModel):
    entries_by_product_id: dict[int, RestCartEntry]
    last_update: datetime


class RestCartManager(CartManager):
    def __init__(self, manager_url: str, manager_access_key: str) -> None:
        super().__init__()
        self.manager_url = manager_url
        self.manager_access_key = manager_access_key

    def initialize(self, available_count_by_product_id: dict[int, int]) -> None:
        requests.put(
            f"{self.manager_url}/state",
            json={
                "cart_by_user_id": {},
                "state_by_product": {
                    product_id: {
                        "product_id": product_id,
                        "total_count": total_count,
                        "already_put": 0,
                    }
                    for product_id, total_count in available_count_by_product_id.items()
                },
            },
        )

    def put_in_cart(self, product_id: int, user_id: int) -> None:
        requests.post(f"{self.manager_url}/cart/{user_id}/{product_id}/increment")

    def remove_from_cart(self, product_id: int, user_id: int) -> None:
        requests.post(f"{self.manager_url}/cart/{user_id}/{product_id}/decrement")

    def get_cart(self, user_id: int) -> Cart:
        response = requests.get(f"{self.manager_url}/cart/{user_id}")
        rest_cart = RestCart(**response.json())
        return Cart(
            user_id=user_id,
            amount_by_product_id={
                product_id: entry.unit_count
                for product_id, entry in rest_cart.entries_by_product_id.items()
            },
        )

    def checkout(self, user_id: int) -> None:
        requests.post(f"{self.manager_url}/cart/{user_id}/checkout")

    def reduce_available_count(self, product_id: int, amount: int) -> None:
        requests.post(f"{self.manager_url}/product/{product_id}/reduce?amount={amount}")

    def increase_available_count(self, product_id: int, amount: int) -> None:
        requests.post(
            f"{self.manager_url}/product/{product_id}/increase?amount={amount}"
        )
