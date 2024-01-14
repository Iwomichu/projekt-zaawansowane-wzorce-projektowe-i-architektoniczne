from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session

from zwpa.model import (
    SupplyStatus,
    SupplyTransportRequest,
    TransportRequest,
    WarehouseProduct,
)


class HandleArrivingSupplyWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker

    def handle_arrival_if_transport_was_supply(self, transport_id: int) -> None:
        with self.session_maker() as session:
            supply_transport_request = session.execute(
                select(SupplyTransportRequest)
                .join(TransportRequest)
                .where(TransportRequest.transport_id == transport_id)
            ).scalar_one_or_none()
            if supply_transport_request is None:
                return
            warehouse_product = session.execute(
                select(WarehouseProduct)
                .where(
                    WarehouseProduct.product_id
                    == supply_transport_request.supply.product_id
                )
                .where(
                    WarehouseProduct.warehouse_id
                    == supply_transport_request.supply.warehouse_id
                )
            ).scalar_one_or_none()
            if warehouse_product is None:
                warehouse_product = WarehouseProduct(
                    warehouse_id=supply_transport_request.supply.warehouse_id,
                    product_id=supply_transport_request.supply.product_id,
                    current_count=0,
                )
                session.add(warehouse_product)
            warehouse_product.current_count = supply_transport_request.supply.unit_count
            supply_transport_request.supply.status = SupplyStatus.COMPLETE
            session.commit()
