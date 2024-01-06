from sqlalchemy import select
from tests.fixtures import Fixtures
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import TransportOffer, TransportStatus, UserRole
from zwpa.workflows.transport.CreateTransportOfferForRequestWorkflow import (
    CreateTransportOfferForRequestWorkflow,
)
from zwpa.workflows.transport.ListTransportRequestsWorkflow import (
    ListTransportRequestsWorkflow,
)


class TransportTestCase(TestCaseWithDatabase):
    def test_transporter_can_list_transport_requests(self):
        # given
        with self.session_maker() as session:
            transporter_id = Fixtures.new_user(session).id
            Fixtures.new_role_assignment(
                session, role=UserRole.TRANSPORT, user_id=transporter_id
            )
            transport_1 = Fixtures.new_transport(session)
            transport_2 = Fixtures.new_transport(
                session, status=TransportStatus.COMPLETE
            )
            available_request_id = Fixtures.new_transport_request(
                session, transport_id=transport_1.id
            ).id
            Fixtures.new_transport_request(session, transport_id=transport_2.id)
            session.commit()
        workflow = ListTransportRequestsWorkflow(
            self.session_maker, Fixtures.new_today_provider()
        )
        # when
        result = workflow.list_available_transport_requests(transporter_id)
        expected = [
            Fixtures.new_transport_request_view(request_id=available_request_id)
        ]

        # then
        self.assertCountEqual(expected, result)

    def test_transport_can_create_transport_offer_for_request(self):
        # given
        with self.session_maker() as session:
            transporter_id = Fixtures.new_user(session).id
            Fixtures.new_role_assignment(
                session, role=UserRole.TRANSPORT, user_id=transporter_id
            )
            transport_id = Fixtures.new_transport(session).id
            available_request_id = Fixtures.new_transport_request(
                session, transport_id=transport_id
            ).id
            session.commit()

        workflow = CreateTransportOfferForRequestWorkflow(self.session_maker)

        # when
        workflow.create_transport_offer_for_request(
            transporter_id, available_request_id
        )

        # then
        with self.session_maker() as session:
            transport_offer = session.execute(
                select(TransportOffer)
                .where(TransportOffer.transport_id == transport_id)
                .where(TransportOffer.transporter_id == transporter_id)
            ).scalar_one_or_none()
            self.assertIsNotNone(transport_offer)

    def test_clerk_can_list_transport_offers_for_request(self):
        # given
        with self.session_maker() as session:
            transporter_id = Fixtures.new_user(session).id
            Fixtures.new_role_assignment(
                session, role=UserRole.TRANSPORT, user_id=transporter_id
            )
            transport_id = Fixtures.new_transport(session).id
            available_request_id = Fixtures.new_transport_request(
                session, transport_id=transport_id
            ).id
            session.commit()
