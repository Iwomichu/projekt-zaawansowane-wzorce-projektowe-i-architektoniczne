from __future__ import annotations
from dataclasses import dataclass

from zwpa.model import Supply, SupplyStatus
from zwpa.workflows.client_requests.HandleClientRequestAcceptanceFormWorkflow import (
    WarehouseView,
)
from zwpa.workflows.client_requests.HandleClientRequestFormWorkflow import ProductView


@dataclass(eq=True)
class SupplyView:
    id: int
    unit_count: int
    status: SupplyStatus
    product: ProductView
    warehouse: WarehouseView

    @staticmethod
    def from_supply(supply: Supply) -> SupplyView:
        return SupplyView(
            id=supply.id,
            unit_count=supply.unit_count,
            status=supply.status,
            product=ProductView.from_product(supply.product),
            warehouse=WarehouseView.from_warehouse(supply.warehouse),
        )
