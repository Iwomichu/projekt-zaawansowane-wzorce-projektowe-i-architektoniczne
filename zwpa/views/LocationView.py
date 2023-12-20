from __future__ import annotations
from dataclasses import dataclass
from zwpa.model import Location


@dataclass(eq=True)
class LocationView:
    id: int
    longitude: float
    latitude: float
    label: str | None = None

    @staticmethod
    def from_location(location: Location) -> LocationView:
        return LocationView(
            id=location.id,
            label=location.label,
            longitude=location.longitude,
            latitude=location.latitude,
        )
