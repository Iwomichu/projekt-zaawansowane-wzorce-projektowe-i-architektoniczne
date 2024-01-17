from dataclasses import dataclass

from zwpa.model import TransportStatus


@dataclass
class RetailTransportView:
    transport_id: int
    product_count: int
    transport_status: TransportStatus
