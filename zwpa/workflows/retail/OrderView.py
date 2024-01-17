from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from zwpa.model import OrderStatus

from zwpa.workflows.retail.RetailStatusProductView import RetailStatusProductView
from zwpa.workflows.retail.RetailTransportView import RetailTransportView


@dataclass
class OrderView:
    id: int
    first_name: str
    last_name: str
    price: Decimal
    destination_location_longitude: float
    destination_location_latitude: float
    products: list[RetailStatusProductView]
    transports: list[RetailTransportView]
    status: OrderStatus
