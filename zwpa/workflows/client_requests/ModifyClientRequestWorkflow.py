from datetime import datetime, time
from decimal import Decimal


class ModifyClientRequestWorkflow:
    def add_new_client_request(
        self,
        user_id: int,
        new_price: Decimal,
        new_unit_count: int,
        new_request_deadline: datetime,
        new_transport_deadline: datetime,
        new_supply_time_window: tuple[time, time],
        new_destination: tuple[float, float],
    ) -> None:
        pass
