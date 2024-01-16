from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from zwpa.workflows.retail.RetailStatusProductView import RetailStatusProductView
from zwpa.workflows.retail.RetailTransportView import RetailTransportView


class OrderStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"

    # TODO: Move that to model


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
