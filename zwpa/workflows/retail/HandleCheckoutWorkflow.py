from datetime import time, timedelta
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import (
    Location,
    Order,
    OrderPersonalInformation,
    OrderPosition,
    OrderTransportRequest,
    Product,
    TimeWindow,
    Transport,
    TransportRequest,
    TransportStatus,
    WarehouseProduct,
)
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import (
    DefaultTodayProvider,
    TodayProvider,
)
from zwpa.workflows.retail.CartManager import Cart, CartManager
from zwpa.workflows.retail.RetailProductView import PersonalizedRetailProductView
from zwpa.workflows.retail.RetailTransportPriceCalculator import (
    RetailTransportPriceCalculator,
)
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class HandleCheckoutWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker[Session],
        cart_manager: CartManager,
        retail_transport_price_calculator: RetailTransportPriceCalculator,
        today_provider: TodayProvider = DefaultTodayProvider(),
    ) -> None:
        self.session_maker = session_maker
        self.cart_manager = cart_manager
        self.retail_transport_price_calculator = retail_transport_price_calculator
        self.today_provider = today_provider

        self.user_role_checker = UserRoleChecker(self.session_maker)

    def handle_checkout(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        destination_longitude: float,
        destination_latitude: float,
    ) -> None:
        with self.session_maker() as session:
            cart = self.cart_manager.get_cart(user_id)
            order = self.create_order_related_entities(
                session,
                user_id,
                first_name=first_name,
                last_name=last_name,
                destination_latitude=destination_latitude,
                destination_longitude=destination_longitude,
                cart=cart,
            )
            for product_id, amount in cart.amount_by_product_id.items():
                amount_from_warehouse_by_warehouse_product_id = (
                    self.reduce_product_amount_in_warehouses(
                        session, product_id=product_id, amount=amount
                    )
                )
                self.create_transport_related_entities(
                    session,
                    order,
                    amount_from_warehouse_by_warehouse_product_id,
                )
            self.cart_manager.checkout(user_id)

    def reduce_product_amount_in_warehouses(
        self, session: Session, product_id: int, amount: int
    ) -> dict[int, int]:
        current_amount = amount
        warehouse_product_id_to_count = {}
        warehouse_products = (
            session.query(WarehouseProduct)
            .where(WarehouseProduct.product_id == product_id)
            .order_by(WarehouseProduct.current_count)
            .all()
        )
        for warehouse_product in warehouse_products:
            if warehouse_product.current_count <= current_amount:
                warehouse_product.current_count -= current_amount
                warehouse_product_id_to_count[warehouse_product.id] = current_amount
                break
            else:
                current_amount -= warehouse_product.current_count
                warehouse_product_id_to_count[
                    warehouse_product.id
                ] = warehouse_product.current_count
                warehouse_product.current_count = 0
        return warehouse_product_id_to_count

    def create_transport_related_entities(
        self,
        session: Session,
        order: Order,
        warehouse_product_id_to_count: dict[int, int],
    ) -> None:
        today = self.today_provider.today()
        transport_request_deadline = today + timedelta(days=3.0)
        time_window = TimeWindow(start=time(7, 00), end=time(19, 00))
        session.add(time_window)
        for warehouse_product_id, amount in warehouse_product_id_to_count.items():
            warehouse = session.get_one(
                WarehouseProduct, warehouse_product_id
            ).warehouse
            transport = Transport(
                unit_count=amount,
                price=self.retail_transport_price_calculator.calculate_price(
                    warehouse_longitude=warehouse.location.longitude,
                    warehouse_latitude=warehouse.location.latitude,
                    destination_latitude=order.destination.latitude,
                    destination_longitude=order.destination.longitude,
                ),
                status=TransportStatus.REQUESTED,
                pickup_location_id=warehouse.location_id,
                destination_location=order.destination,
                load_time_window=warehouse.load_time_windows[0],
                destination_time_window=time_window,
            )
            transport_request = TransportRequest(
                request_deadline=transport_request_deadline, transport=transport
            )
            order_transport_request = OrderTransportRequest(
                order=order,
                transport_request=transport_request,
            )
            session.add_all([transport, transport_request, order_transport_request])

    def create_order_related_entities(
        self,
        session: Session,
        user_id: int,
        first_name: str,
        last_name: str,
        destination_longitude: float,
        destination_latitude: float,
        cart: Cart,
    ) -> Order:
        destination = Location(
            longitude=destination_longitude, latitude=destination_latitude
        )
        products_by_id = {
            product.id: product
            for product in session.query(Product)
            .where(Product.id.in_(cart.amount_by_product_id.keys()))
            .all()
        }
        order = Order(
            user_id=user_id,
            total_price=sum(
                product.retail_price for product in products_by_id.values()
            ),
            destination=destination,
        )
        order_personal_info = OrderPersonalInformation(
            first_name=first_name,
            last_name=last_name,
            order=order,
        )
        order_positions = [
            OrderPosition(
                product_id=product_id,
                amount=count,
                order=order,
            )
            for product_id, count in cart.amount_by_product_id.items()
        ]
        session.add(order_personal_info)
        session.add(order)
        session.add_all(order_positions)
        return order
