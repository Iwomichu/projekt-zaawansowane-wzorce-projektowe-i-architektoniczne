from datetime import date
from decimal import Decimal
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import (
    SupplyOffer,
    SupplyReceipt,
    SupplyRequest,
    SupplyStatus,
    SupplyTransportRequest,
    Transport,
    TransportRequest,
    UserRole,
)
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import (
    DefaultTodayProvider,
    TodayProvider,
)
from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class AcceptRequestedSupplyOfferWorkflow:
    def __init__(
        self,
        session_maker: sessionmaker[Session],
        today_provider: TodayProvider = DefaultTodayProvider(),
    ) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)
        self.today_provider = today_provider

    def accept_supply_offer(
        self,
        user_id: int,
        supply_offer_id: int,
        transport_price: Decimal,
        transport_request_deadline: date,
    ) -> None:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        with self.session_maker() as session:
            supply_offer = (
                session.query(SupplyOffer)
                .where(SupplyOffer.id == supply_offer_id)
                .one()
            )
            self._update_supply_offer(supply_offer)
            self._create_transport_entities(
                session, supply_offer, transport_price, transport_request_deadline
            )
            self._create_receipt(session, supply_offer, clerk_id=user_id)
            session.commit()

    def _create_receipt(
        self, session: Session, supply_offer: SupplyOffer, clerk_id: int
    ) -> None:
        supply_request_id = (
            session.query(SupplyRequest)
            .where(SupplyRequest.supply_id == supply_offer.supply_id)
            .one()
            .id
        )
        receipt = SupplyReceipt(
            offer_acceptance_datetime=self.today_provider.today(),
            request_id=supply_request_id,
            offer_id=supply_offer.id,
            clerk_id=clerk_id,
        )
        session.add(receipt)

    def _update_supply_offer(self, supply_offer: SupplyOffer) -> None:
        supply_offer.accepted = True
        supply_offer.supply.status = SupplyStatus.OFFER_ACCEPTED

    def _create_transport_entities(
        self,
        session: Session,
        supply_offer: SupplyOffer,
        transport_price: Decimal,
        transport_request_deadline: date,
    ) -> None:
        transport = Transport(
            unit_count=supply_offer.supply.unit_count,
            price=transport_price,
            pickup_location_id=supply_offer.source_location_id,
            destination_location_id=supply_offer.supply.warehouse.location_id,
            load_time_window_id=supply_offer.load_time_window_id,
            destination_time_window_id=supply_offer.supply.supply_time_window_id,
        )
        transport_request = TransportRequest(
            request_deadline=transport_request_deadline,
            accepted=False,
            transport=transport,
        )
        supply_transport_request = SupplyTransportRequest(
            supply_id=supply_offer.supply_id,
            transport_request=transport_request,
        )
        session.add(transport)
        session.add(transport_request)
        session.add(supply_transport_request)
