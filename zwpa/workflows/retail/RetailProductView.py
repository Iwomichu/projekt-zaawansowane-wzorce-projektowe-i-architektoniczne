from dataclasses import field, dataclass
from decimal import Decimal


@dataclass
class RetailProductView:
    id: int
    label: str
    unit: str
    price: Decimal
    available: int


@dataclass
class PersonalizedRetailProductView(RetailProductView):
    already_in_cart: int
    total: Decimal = field(init=False)

    def __post_init__(self):
        self.total = self.price * self.already_in_cart
