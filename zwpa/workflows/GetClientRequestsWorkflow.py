from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select
from zwpa.model import ClientRequest, User, UserRole


@dataclass(eq=True)
class ClientRequestView:
    id: int
    client_id: int
    price: Decimal
    unit_count: int
    request_deadline: date
    transport_deadline: date
    destination_longitude: float
    destination_latitude: float
    supply_time_window_start: time
    supply_time_window_end: time
    product_name: str
    product_unit: str
    accepted: bool

    @staticmethod
    def from_client_request(client_request: ClientRequest):
        return ClientRequestView(
            id=client_request.id,
            client_id=client_request.client_id,
            price=client_request.price,
            unit_count=client_request.unit_count,
            request_deadline=client_request.request_deadline,
            transport_deadline=client_request.transport_deadline,
            destination_longitude=client_request.destination.longitude,
            destination_latitude=client_request.destination.latitude,
            product_name=client_request.product.label,
            product_unit=client_request.product.unit,
            supply_time_window_start=client_request.supply_time_window.start,
            supply_time_window_end=client_request.supply_time_window.end,
            accepted=client_request.accepted,
        )


class UserLacksRoleException(Exception):
    pass


class GetClientRequestsWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker,
    ) -> None:
        self.session_maker = session_maker

    def get_all_client_requests_workflow(self, user_id: int) -> list[ClientRequestView]:
        if not self.__is_user_of_role(user_id=user_id, role=UserRole.CLERK):
            raise UserLacksRoleException()
        with self.session_maker() as session:
            return [
                ClientRequestView.from_client_request(request)
                for request in self.__get_client_requests(session=session)
            ]

    def get_my_client_requests_workflow(self, user_id: int) -> list[ClientRequestView]:
        if not self.__is_user_of_role(user_id=user_id, role=UserRole.CLIENT):
            raise UserLacksRoleException()
        with self.session_maker() as session:
            return [
                ClientRequestView.from_client_request(request)
                for request in self.__get_client_requests(
                    session=session, client_id=user_id
                )
            ]

    def __is_user_of_role(self, user_id: int, role: UserRole) -> bool:
        with self.session_maker() as session:
            user_roles = [
                assignment.role for assignment in session.get_one(User, user_id).roles
            ]
            return role in user_roles

    def __get_client_requests(
        self, session: Session, client_id: int | None = None
    ) -> list[ClientRequest]:
        query = select(ClientRequest)
        if client_id is not None:
            query = query.where(ClientRequest.client_id == client_id)
        return [row for row in session.execute(query).scalars()]
