from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from zwpa.model import SupplyRequest

from zwpa.views.SupplyView import SupplyView


@dataclass(eq=True)
class SupplyRequestView:
    id: int
    request_deadline: date
    supply: SupplyView

    @staticmethod
    def from_supply_request(supply_request: SupplyRequest) -> SupplyRequestView:
        return SupplyRequestView(
            id=supply_request.id,
            request_deadline=supply_request.request_deadline,
            supply=SupplyView.from_supply(supply_request.supply),
        )
