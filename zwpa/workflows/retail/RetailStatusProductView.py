from dataclasses import dataclass


@dataclass
class RetailStatusProductView:
    id: int
    label: str
    count: int
