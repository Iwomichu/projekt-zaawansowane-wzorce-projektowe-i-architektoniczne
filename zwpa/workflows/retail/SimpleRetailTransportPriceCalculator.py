from decimal import Decimal

from zwpa.workflows.retail.RetailTransportPriceCalculator import (
    RetailTransportPriceCalculator,
)


class SimpleRetailTransportPriceCalculator(RetailTransportPriceCalculator):
    def __init__(self, price_per_degree: Decimal = Decimal(600.0)) -> None:
        super().__init__()
        self.price_per_degree = price_per_degree

    def calculate_price(
        self,
        warehouse_longitude: float,
        warehouse_latitude: float,
        destination_longitude: float,
        destination_latitude: float,
    ) -> Decimal:
        degrees = (
            abs(warehouse_longitude - destination_longitude) ** 2
            + abs(warehouse_latitude - destination_latitude) ** 2
        ) ** (1 / 2)
        return self.price_per_degree * Decimal(degrees)
