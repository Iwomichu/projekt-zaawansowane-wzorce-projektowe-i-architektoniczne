from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import ClientRequest, TimeWindow, UserRole, Warehouse
from zwpa.workflows.client_requests.GetClientRequestsWorkflow import ClientRequestView

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


@dataclass(eq=True)
class TimeWindowView:
    id: int
    start: time
    end: time

    @staticmethod
    def from_time_window(time_window: TimeWindow) -> TimeWindowView:
        return TimeWindowView(
            id=time_window.id, start=time_window.start, end=time_window.end
        )


@dataclass(eq=True)
class WarehouseView:
    id: int
    label: str
    load_time_windows: list[TimeWindowView]

    @staticmethod
    def from_warehouse(warehouse: Warehouse) -> WarehouseView:
        return WarehouseView(
            id=warehouse.id,
            label=warehouse.label,
            load_time_windows=[
                TimeWindowView(
                    id=time_window.id, start=time_window.start, end=time_window.end
                )
                for time_window in warehouse.load_time_windows
            ],
        )


@dataclass(eq=True)
class ClientRequestAcceptanceFormData:
    client_request: ClientRequestView
    warehouses: list[WarehouseView]


class HandleClientRequestAcceptanceFormWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(session_maker)

    def get_form_data(
        self, user_id: int, client_request_id: int
    ) -> ClientRequestAcceptanceFormData:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        with self.session_maker() as session:
            client_request = session.get(ClientRequest, client_request_id)
            warehouses = session.execute(select(Warehouse)).scalars()
            return ClientRequestAcceptanceFormData(
                client_request=ClientRequestView.from_client_request(client_request),
                warehouses=[
                    WarehouseView.from_warehouse(warehouse) for warehouse in warehouses
                ],
            )
