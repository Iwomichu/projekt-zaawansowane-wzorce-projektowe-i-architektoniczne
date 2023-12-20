from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from zwpa.model import SupplyOffer
from zwpa.views.LocationView import LocationView

from zwpa.views.SupplyView import SupplyView
from zwpa.workflows.client_requests.HandleClientRequestAcceptanceFormWorkflow import (
    TimeWindowView,
)


@dataclass(eq=True)
class SupplyOfferView:
    id: int
    price: Decimal
    transport_deadline: date
    accepted: bool
    supplier_login: str
    supply: SupplyView
    source_location: LocationView
    load_time_window: TimeWindowView

    @staticmethod
    def from_supply_offer(supply_offer: SupplyOffer) -> SupplyOfferView:
        return SupplyOfferView(
            id=supply_offer.id,
            price=supply_offer.price,
            transport_deadline=supply_offer.transport_deadline,
            accepted=supply_offer.accepted,
            supplier_login=supply_offer.supplier.login,
            load_time_window=TimeWindowView.from_time_window(
                supply_offer.load_time_window
            ),
            supply=SupplyView.from_supply(supply_offer.supply),
            source_location=LocationView.from_location(supply_offer.source_location),
        )
