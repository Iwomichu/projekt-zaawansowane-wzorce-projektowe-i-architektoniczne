from sqlalchemy import select
from tests.fixtures import Fixtures
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import Transport, TransportOffer, TransportOfferStatus, TransportStatus, UserRole
from zwpa.workflows.transport.AcceptTransportOfferForRequestWorkflow import (
    AcceptTransportOfferForRequestWorkflow,
)
from zwpa.workflows.transport.CreateTransportOfferForRequestWorkflow import (
    CreateTransportOfferForRequestWorkflow,
)
from zwpa.workflows.transport.ListTransportOffersForRequestWorkflow import (
    ListTransportOffersForRequestWorkflow,
    TransportOfferView,
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

    def test_list_transport_requests_doesnt_show_requests_with_already_accepted_offers(self):
        # given
        with self.session_maker() as session:
            transporter = Fixtures.new_user_with_roles(
                session, roles=[UserRole.TRANSPORT]
            )
            transporter_id = transporter.id
            transport_accepted_id = Fixtures.new_transport(session, status=TransportStatus.OFFER_ACCEPTED).id
            Fixtures.new_transport_request(
                session, transport_id=transport_accepted_id
            ).id
            Fixtures.new_transport_offer(
                session, transport_accepted_id, transporter_id
            ).id

            transport_complete_id = Fixtures.new_transport(session, status=TransportStatus.OFFER_ACCEPTED).id
            Fixtures.new_transport_request(
                session, transport_id=transport_complete_id
            ).id
            Fixtures.new_transport_offer(
                session, transport_complete_id, transporter_id
            ).id
            session.commit()
        workflow = ListTransportRequestsWorkflow(
            self.session_maker, Fixtures.new_today_provider()
        )
        # when
        result = workflow.list_available_transport_requests(transporter_id)
        expected = []

        # then
        self.assertCountEqual(expected, result)

    def test_transporter_can_create_transport_offer_for_request(self):
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
            clerk_id = Fixtures.new_user_with_roles(session, roles=[UserRole.CLERK]).id
            transporter = Fixtures.new_user_with_roles(
                session, roles=[UserRole.TRANSPORT]
            )
            transporter_id = transporter.id
            transporter_login = transporter.login
            transport_id = Fixtures.new_transport(session).id
            available_request_id = Fixtures.new_transport_request(
                session, transport_id=transport_id
            ).id
            transport_offer_id = Fixtures.new_transport_offer(
                session, transport_id, transporter_id
            ).id
            session.commit()

        workflow = ListTransportOffersForRequestWorkflow(self.session_maker)
        # when
        expected = [
            TransportOfferView(
                transport_offer_id=transport_offer_id,
                transporter_id=transporter_id,
                transporter_login=transporter_login,
            )
        ]
        result = workflow.list_transport_offer_for_request(
            user_id=clerk_id, transport_request_id=available_request_id
        )

        # then
        self.assertCountEqual(expected, result)

    def test_clerk_can_accept_transport_offer(self):
        # given
        with self.session_maker() as session:
            clerk_id = Fixtures.new_user_with_roles(session, roles=[UserRole.CLERK]).id
            transporter = Fixtures.new_user_with_roles(
                session, roles=[UserRole.TRANSPORT]
            )
            transporter_id = transporter.id
            transport_id = Fixtures.new_transport(session).id
            other_transporter_id = Fixtures.new_user_with_roles(
                session, roles=[UserRole.TRANSPORT]
            ).id
            available_request_id = Fixtures.new_transport_request(
                session, transport_id=transport_id
            ).id
            transport_offer_id = Fixtures.new_transport_offer(
                session, transport_id, transporter_id
            ).id
            other_transport_offer_id = Fixtures.new_transport_offer(
                session, transport_id, other_transporter_id
            ).id
            session.commit()

        workflow = AcceptTransportOfferForRequestWorkflow(
            self.session_maker, today_provider=Fixtures.new_today_provider()
        )

        # when
        workflow.accept_transport_offer_for_request(
            user_id=clerk_id,
            transport_offer_id=transport_offer_id,
            transport_request_id=available_request_id,
        )

        # then
        with self.session_maker() as session:
            transport = session.get_one(Transport, transport_id)
            self.assertEqual(transport.status, TransportStatus.OFFER_ACCEPTED)
            transport_offer = session.get_one(TransportOffer, transport_offer_id)
            self.assertEqual(transport_offer.status, TransportOfferStatus.ACCEPTED)
            other_transport_offer = session.get_one(TransportOffer, other_transport_offer_id)
            self.assertEqual(other_transport_offer.status, TransportOfferStatus.REJECTED)
        # transport status changed
        # TODO: manifest generated
