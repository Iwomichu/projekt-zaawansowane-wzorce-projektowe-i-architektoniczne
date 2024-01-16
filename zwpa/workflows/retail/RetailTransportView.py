from dataclasses import dataclass

from zwpa.model import TransportStatus


@dataclass
class RetailTransportView:
    transport_id: int
    product_label: str
    product_count: int
    transport_status: TransportStatus
