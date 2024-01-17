from abc import ABC, abstractmethod
from decimal import Decimal


class RetailTransportPriceCalculator(ABC):
    @abstractmethod
    def calculate_price(
        self,
        warehouse_longitude: float,
        warehouse_latitude: float,
        destination_longitude: float,
        destination_latitude: float,
    ) -> Decimal:
        pass
