from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session

from zwpa.model import (
    OrderStatus,
    OrderTransportRequest,
    TransportRequest,
    TransportStatus,
)


class HandleArrivingRetailPackageWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker

    def handle_arrival_if_transport_was_retail(self, transport_id: int) -> None:
        with self.session_maker() as session:
            order_transport_request = session.execute(
                select(OrderTransportRequest)
                .join(TransportRequest)
                .where(TransportRequest.transport_id == transport_id)
            ).scalar_one_or_none()
            if order_transport_request is None:
                return
            all_other_order_transport_arrived = all(
                transport_request.transport_request.transport.status
                == TransportStatus.COMPLETE
                for transport_request in order_transport_request.order.transport_requests
                if transport_request.transport_request.transport_id != transport_id
            )
            if all_other_order_transport_arrived:
                order_transport_request.order.status = OrderStatus.FINISHED
            session.commit()
