from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import Order, OrderPosition, OrderTransportRequest, Product
from zwpa.workflows.retail.CartManager import CartManager
from zwpa.workflows.retail.OrderView import OrderView
from zwpa.workflows.retail.RetailProductView import PersonalizedRetailProductView
from zwpa.workflows.retail.RetailStatusProductView import RetailStatusProductView
from zwpa.workflows.retail.RetailTransportView import RetailTransportView
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


def _create_product_view(position: OrderPosition) -> RetailStatusProductView:
    return RetailStatusProductView(
        id=position.product_id, label=position.product.label, count=position.amount
    )


def _create_transport_view(
    order_transport_request: OrderTransportRequest,
) -> RetailTransportView:
    return RetailTransportView(
        transport_id=order_transport_request.transport_request.transport.id,
        product_count=order_transport_request.transport_request.transport.unit_count,
        transport_status=order_transport_request.transport_request.transport.status,
    )


def _create_order_view(order: Order) -> OrderView:
    return OrderView(
        id=order.id,
        first_name=order.order_personal_information.first_name,
        last_name=order.order_personal_information.last_name,
        destination_location_latitude=order.destination.latitude,
        destination_location_longitude=order.destination.longitude,
        price=order.total_price,
        status=order.status,
        products=[_create_product_view(product) for product in order.positions],
        transports=[
            _create_transport_view(transport) for transport in order.transport_requests
        ],
    )


class GetOrderViewsWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker[Session],
    ) -> None:
        self.session_maker = session_maker

        self.user_role_checker = UserRoleChecker(self.session_maker)

    def get_order_views(self, user_id: int) -> list[OrderView]:
        with self.session_maker() as session:
            orders = session.query(Order).where(Order.user_id == user_id).all()
            return [_create_order_view(order) for order in orders]

    def get_order_view(self, order_id: int) -> OrderView:
        with self.session_maker() as session:
            order = session.query(Order).where(Order.id == order_id).one()
            return _create_order_view(order)
