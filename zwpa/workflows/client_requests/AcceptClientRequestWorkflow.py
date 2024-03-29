from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session

from zwpa.model import (
    ClientRequest,
    ClientTransportRequest,
    Transport,
    TransportRequest,
    TransportStatus,
    User,
    UserRole,
    Warehouse,
    WarehouseProduct,
)
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import (
    DefaultTodayProvider,
    TodayProvider,
)
from zwpa.exceptions.UserLacksRoleException import UserLacksRoleException


class RequestAlreadyAccepted(Exception):
    pass


class RequestTimedOut(Exception):
    pass


class ChosenWarehouseDoesNotSatisfyNeededCount(Exception):
    pass


class AcceptClientRequestWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker,
        today_provider: TodayProvider = DefaultTodayProvider(),
    ) -> None:
        self.session_maker = session_maker
        self.today_provider = today_provider

    def accept_client_request(
        self,
        user_id: int,
        client_request_id: int,
        warehouse_id: int,
        transport_request_deadline: date,
        time_window_id: int,
        price_for_transport: Decimal,
    ) -> None:
        with self.session_maker() as session:
            if not self.__is_user_of_role(session, user_id, role=UserRole.CLERK):
                raise UserLacksRoleException()
            self.__validate_request(session, client_request_id, warehouse_id)
            self.__add_new_transport_with_request(
                session=session,
                client_request_id=client_request_id,
                source_warehouse_id=warehouse_id,
                load_time_window_id=time_window_id,
                transport_request_deadline=transport_request_deadline,
                price=price_for_transport,
            )
            self.__mark_request_as_accepted(
                session=session, client_request_id=client_request_id
            )
            self.__decrease_count_in_warehouse(
                session, client_request_id, source_warehouse_id=warehouse_id
            )
            session.commit()

    def __is_user_of_role(self, session: Session, user_id: int, role: UserRole) -> bool:
        user_roles = [
            assignment.role for assignment in session.get_one(User, user_id).roles
        ]
        return role in user_roles

    def __validate_request(self, session: Session, client_request_id: int, source_warehouse_id: int) -> None:
        client_request: ClientRequest = session.get_one(
            ClientRequest, client_request_id
        )
        warehouse_product = session.execute(
            select(WarehouseProduct)
            .where(WarehouseProduct.warehouse_id == source_warehouse_id)
            .where(WarehouseProduct.product_id == client_request.product_id)
        ).scalar_one()
        if client_request.accepted:
            raise RequestAlreadyAccepted()
        if client_request.request_deadline < self.today_provider.today().date():
            raise RequestTimedOut()
        if warehouse_product.current_count < client_request.unit_count:
            raise ChosenWarehouseDoesNotSatisfyNeededCount()

    def __add_new_transport_with_request(
        self,
        session: Session,
        client_request_id: int,
        source_warehouse_id: int,
        transport_request_deadline: date,
        load_time_window_id: int,
        price: Decimal,
    ) -> None:
        warehouse = session.get_one(Warehouse, source_warehouse_id)
        client_request = session.get_one(ClientRequest, client_request_id)
        transport = Transport(
            unit_count=client_request.unit_count,
            pickup_location_id=warehouse.location_id,
            destination_location_id=client_request.destination_id,
            load_time_window_id=load_time_window_id,
            destination_time_window_id=client_request.supply_time_window_id,
            price=price,
            status=TransportStatus.REQUESTED,
        )
        transport_request = TransportRequest(
            request_deadline=transport_request_deadline,
            transport=transport,
        )
        client_transport_request = ClientTransportRequest(
            client_request=client_request, transport_request=transport_request
        )
        session.add(transport)
        session.add(transport_request)
        session.add(client_transport_request)

    def __mark_request_as_accepted(
        self, session: Session, client_request_id: int
    ) -> None:
        session.get_one(ClientRequest, client_request_id).accepted = True

    def __decrease_count_in_warehouse(
        self,
        session: Session,
        client_request_id: int,
        source_warehouse_id: int,
    ) -> None:
        client_request = session.get_one(ClientRequest, client_request_id)
        warehouse_product = session.execute(
            select(WarehouseProduct)
            .where(WarehouseProduct.warehouse_id == source_warehouse_id)
            .where(WarehouseProduct.product_id == client_request.product_id)
        ).scalar_one()
        warehouse_product.current_count -= client_request.unit_count
