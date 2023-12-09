from datetime import datetime


class AcceptClientRequestWorkflow:
    def accept_client_request(
        self,
        user_id: int,
        client_request_id: int,
        source_warehouse_id: int,
        transport_request_deadline: datetime,
        load_time_window_id: int,
    ) -> None:
        pass
