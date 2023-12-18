from datetime import date, time
from decimal import Decimal
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import Location, SupplyOffer, SupplyRequest, TimeWindow, UserRole

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class CreateNewSupplyOfferWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def create_new_supply_offer_for_request(
        self,
        price: Decimal,
        transport_deadline: date,
        supply_request_id: int,
        supplier_id: int,
        load_time_window_start: time,
        load_time_window_end: time,
        source_longitude: float,
        source_latitude: float,
    ) -> None:
        self.user_role_checker.assert_user_of_role(
            user_id=supplier_id, role=UserRole.SUPPLIER
        )
        with self.session_maker() as session:
            time_window = TimeWindow(
                start=load_time_window_start, end=load_time_window_end
            )
            location = Location(longitude=source_longitude, latitude=source_latitude)
            supply_id = (
                session.query(SupplyRequest)
                .where(SupplyRequest.id == supply_request_id)
                .one()
                .supply_id
            )
            session.add(
                SupplyOffer(
                    price=price,
                    transport_deadline=transport_deadline,
                    supply_id=supply_id,
                    supplier_id=supplier_id,
                    load_time_window=time_window,
                    source_location=location,
                    accepted=False,
                )
            )
            session.commit()
