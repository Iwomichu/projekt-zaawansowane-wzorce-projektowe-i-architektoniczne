from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import SupplyOffer, SupplyRequest, UserRole
from zwpa.views.SupplyOfferView import SupplyOfferView

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


class ListSupplyOffersForRequestWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def list_supply_offers_for_request(
        self, user_id: int, supply_request_id: int
    ) -> list[SupplyOfferView]:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        with self.session_maker() as session:
            supply_request = (
                session.query(SupplyRequest)
                .where(SupplyRequest.id == supply_request_id)
                .one()
            )
            supply_offers = (
                session.query(SupplyOffer)
                .where(SupplyOffer.supply_id == supply_request.supply_id)
                .all()
            )
            return [SupplyOfferView.from_supply_offer(offer) for offer in supply_offers]
