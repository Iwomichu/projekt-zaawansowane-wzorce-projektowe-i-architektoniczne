from datetime import date, datetime, time, timezone
from decimal import Decimal
from unittest import skip
from tests.fixtures import (
    PRICE,
    TODAY_DATE,
    TRANSPORT_DEADLINE,
    Fixtures,
    REQUEST_DEADLINE,
    UNIT_COUNT,
)
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import (
    SupplyOffer,
    SupplyReceipt,
    SupplyRequest,
    SupplyStatus,
    SupplyTransportRequest,
    TransportRequest,
    UserRole,
)
from zwpa.views.SupplyOfferView import SupplyOfferView
from zwpa.workflows.supplies.AcceptRequestedSupplyOfferWorkflow import (
    AcceptRequestedSupplyOfferWorkflow,
    AlreadyAcceptedSupplyOfferAcceptAttemptException,
)
from zwpa.workflows.supplies.CreateNewSupplyOfferWorkflow import (
    CreateNewSupplyOfferWorkflow,
)
from zwpa.workflows.supplies.CreateNewSupplyRequestWorkflow import (
    CreateNewSupplyRequestWorkflow,
)
from zwpa.workflows.supplies.HandleSupplyOfferFormWorkflow import (
    HandleSupplyOfferFormWorkflow,
)
from zwpa.workflows.supplies.HandleSupplyRequestFormWorkflow import (
    HandleSupplyRequestFormWorkflow,
)
from zwpa.workflows.supplies.ListSupplyOffersForRequestWorkflow import (
    ListSupplyOffersForRequestWorkflow,
)
from zwpa.workflows.supplies.ListSupplyRequestsWorkflow import (
    ListSupplyRequestsWorkflow,
)


class SupplyTestCase(TestCaseWithDatabase):
    def test_clerk_can_access_supply_request_creation_data(self):
        # given
        workflow = HandleSupplyRequestFormWorkflow(self.session_maker)
        with self.session_maker() as session:
            user_id = Fixtures.new_user_with_roles(session, roles=[UserRole.CLERK]).id
            warehouse = Fixtures.new_warehouse(session)
            warehouse_id = warehouse.id
            time_window_id = warehouse.load_time_windows[0].id
            product_id = Fixtures.new_product(session).id
            session.commit()

        # when
        expected = Fixtures.new_supply_request_form_data(
            warehouse_id=warehouse_id,
            time_window_id=time_window_id,
            product_ids=[product_id],
        )
        result = workflow.get_data(user_id)

        # then
        self.assertEqual(expected, result)

    def test_clerk_can_create_supply_request(self):
        # given
        workflow = CreateNewSupplyRequestWorkflow(self.session_maker)
        with self.session_maker() as session:
            user_id = Fixtures.new_user_with_roles(session, roles=[UserRole.CLERK]).id
            product_id = Fixtures.new_product(session).id
            warehouse = Fixtures.new_warehouse(session)
            warehouse_id = warehouse.id
            time_window_id = warehouse.load_time_windows[0].id
            session.commit()

        # when
        workflow.create_new_supply_request(
            user_id=user_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            time_window_id=time_window_id,
            unit_count=UNIT_COUNT,
            request_deadline=REQUEST_DEADLINE,
        )

        # then
        with self.session_maker() as session:
            supply_request = session.query(SupplyRequest).one()
            self.assertEqual(user_id, supply_request.clerk_id)
            self.assertEqual(REQUEST_DEADLINE, supply_request.request_deadline)
            self.assertEqual(warehouse_id, supply_request.supply.warehouse_id)
            self.assertEqual(product_id, supply_request.supply.product_id)
            self.assertEqual(UNIT_COUNT, supply_request.supply.unit_count)
            self.assertEqual(SupplyStatus.REQUESTED, supply_request.supply.status)

    def test_clerk_can_list_supply_requests(self):
        # given
        workflow = ListSupplyRequestsWorkflow(self.session_maker)
        with self.session_maker() as session:
            user_id = Fixtures.new_user_with_roles(session, roles=[UserRole.CLERK]).id
            supply_request = Fixtures.new_supply_request(session)
            session.commit()

            expected = [
                Fixtures.new_supply_request_view(
                    supply_request_id=supply_request.id,
                    supply_id=supply_request.supply_id,
                    product_id=supply_request.supply.product_id,
                    warehouse_id=supply_request.supply.warehouse_id,
                    time_window_id=supply_request.supply.supply_time_window_id,
                )
            ]

        # when
        result = workflow.list_supply_requests(user_id)

        # then
        self.assertCountEqual(expected, result)

    def test_supplier_can_list_supply_requests(self):
        # given
        workflow = ListSupplyRequestsWorkflow(self.session_maker)
        with self.session_maker() as session:
            user_id = Fixtures.new_user_with_roles(
                session, roles=[UserRole.SUPPLIER]
            ).id
            supply_request = Fixtures.new_supply_request(session)
            session.commit()

            expected = [
                Fixtures.new_supply_request_view(
                    supply_request_id=supply_request.id,
                    supply_id=supply_request.supply_id,
                    product_id=supply_request.supply.product_id,
                    warehouse_id=supply_request.supply.warehouse_id,
                    time_window_id=supply_request.supply.supply_time_window_id,
                )
            ]

        # when
        result = workflow.list_supply_requests(user_id)

        # then
        self.assertCountEqual(expected, result)

    def test_listing_of_supply_requests_includes_only_requested_supplies(self):
        # given
        workflow = ListSupplyRequestsWorkflow(self.session_maker)
        with self.session_maker() as session:
            user_id = Fixtures.new_user_with_roles(
                session, roles=[UserRole.SUPPLIER]
            ).id
            supply_accepted = Fixtures.new_supply(
                session, status=SupplyStatus.OFFER_ACCEPTED
            )
            Fixtures.new_supply_request(session, supply_id=supply_accepted.id)
            supply_complete = Fixtures.new_supply(session, status=SupplyStatus.COMPLETE)
            Fixtures.new_supply_request(session, supply_id=supply_complete.id)
            supply_request = Fixtures.new_supply_request(session)
            session.commit()

            expected = [
                Fixtures.new_supply_request_view(
                    supply_request_id=supply_request.id,
                    supply_id=supply_request.supply_id,
                    product_id=supply_request.supply.product_id,
                    warehouse_id=supply_request.supply.warehouse_id,
                    time_window_id=supply_request.supply.supply_time_window_id,
                )
            ]

        # when
        result = workflow.list_supply_requests(user_id)

        # then
        self.assertCountEqual(expected, result)

    def test_supplier_can_access_supply_offer_creation_data(self):
        # given
        workflow = HandleSupplyOfferFormWorkflow(self.session_maker)
        with self.session_maker() as session:
            supplier_id = Fixtures.new_user_with_roles(
                session, roles=[UserRole.SUPPLIER]
            ).id
            supply_request = Fixtures.new_supply_request(session)
            session.commit()
            supply_request_id = supply_request.id
            supply_id = supply_request.supply.id
            warehouse_id = supply_request.supply.warehouse_id
            time_window_id = supply_request.supply.supply_time_window_id
            product_id = supply_request.supply.product_id

        # when
        expected = Fixtures.new_supply_offer_form_data(
            supply_request_id=supply_request_id,
            supply_id=supply_id,
            warehouse_id=warehouse_id,
            time_window_id=time_window_id,
            product_id=product_id,
        )
        result = workflow.get_form_data(
            supplier_id, supply_request_id=supply_request_id
        )

        # then
        self.assertEqual(expected, result)

    def test_supplier_can_create_supply_offer_for_supply_request(self):
        # given
        workflow = CreateNewSupplyOfferWorkflow(self.session_maker)
        price = Decimal(2.0)
        source_longitude = 7.0
        source_latitude = 6.0
        source_load_window_start = time(3, 0)
        source_load_window_end = time(6, 0)
        transport_deadline = date(2025, 6, 1)
        with self.session_maker() as session:
            supplier_id = Fixtures.new_user_with_roles(
                session, roles=[UserRole.SUPPLIER]
            ).id
            supply_request = Fixtures.new_supply_request(session)
            supply_request_id = supply_request.id
            supply_id = supply_request.supply_id
            session.commit()
        # when
        workflow.create_new_supply_offer_for_request(
            price=price,
            transport_deadline=transport_deadline,
            supply_request_id=supply_request_id,
            supplier_id=supplier_id,
            load_time_window_start=source_load_window_start,
            load_time_window_end=source_load_window_end,
            source_longitude=source_longitude,
            source_latitude=source_latitude,
        )
        # then
        with self.session_maker() as session:
            supply_offer = session.query(SupplyOffer).one()
            self.assertEqual(price, supply_offer.price)
            self.assertEqual(source_longitude, supply_offer.source_location.longitude)
            self.assertEqual(source_latitude, supply_offer.source_location.latitude)
            self.assertEqual(
                source_load_window_start, supply_offer.load_time_window.start
            )
            self.assertEqual(source_load_window_end, supply_offer.load_time_window.end)
            self.assertEqual(transport_deadline, supply_offer.transport_deadline)
            self.assertEqual(supplier_id, supply_offer.supplier_id)
            self.assertEqual(supply_id, supply_offer.supply_id)
            self.assertFalse(supply_offer.accepted)

    def test_clerk_can_list_supply_offers_for_request(self):
        # given
        workflow = ListSupplyOffersForRequestWorkflow(self.session_maker)
        with self.session_maker() as session:
            clerk_id = Fixtures.new_user_with_roles(session, roles=[UserRole.CLERK]).id
            supply_request = Fixtures.new_supply_request(session)
            supply_offer = Fixtures.new_supply_offer(
                session, supply_id=supply_request.supply_id
            )
            supply_request_id = supply_request.id
            session.commit()
            expected = [SupplyOfferView.from_supply_offer(supply_offer)]

        # when
        result = workflow.list_supply_offers_for_request(
            user_id=clerk_id, supply_request_id=supply_request_id
        )

        # then
        self.assertCountEqual(expected, result)


class AcceptSupplyOfferTestCase(TestCaseWithDatabase):
    def _clerk_tries_to_accept_supply_offer(self):
        self.price = PRICE
        self.today_datetime = datetime(2020, 1, 1)
        self.transport_request_deadline = TRANSPORT_DEADLINE
        self.workflow = AcceptRequestedSupplyOfferWorkflow(
            self.session_maker,
            today_provider=Fixtures.new_today_provider(self.today_datetime),
        )
        with self.session_maker() as session:
            self.clerk_id = Fixtures.new_user_with_roles(
                session, roles=[UserRole.CLERK]
            ).id
            self.supply_request = Fixtures.new_supply_request(session)
            self.supply_request_id = self.supply_request.id
            self.supply_id = self.supply_request.supply_id
            self.supply_offer_id = Fixtures.new_supply_offer(
                session, supply_id=self.supply_id
            ).id
            session.commit()

        # when
        self.workflow.accept_supply_offer(
            user_id=self.clerk_id,
            supply_offer_id=self.supply_offer_id,
            transport_price=self.price,
            transport_request_deadline=self.transport_request_deadline,
        )

    def test_clerk_cannot_accept_supply_offer_for_already_fulfilled_supply(self):
        self._clerk_tries_to_accept_supply_offer()
        self.assertRaises(
            AlreadyAcceptedSupplyOfferAcceptAttemptException,
            self.workflow.accept_supply_offer,
            user_id=self.clerk_id,
            supply_offer_id=self.supply_offer_id,
            transport_price=self.price,
            transport_request_deadline=self.transport_request_deadline,
        )

    def test_clerk_can_accept_supply_offer(self):
        # given
        self._clerk_tries_to_accept_supply_offer()

        # then
        with self.session_maker() as session:
            supply_offer = (
                session.query(SupplyOffer)
                .where(SupplyOffer.id == self.supply_offer_id)
                .one()
            )
            self.assertTrue(supply_offer.accepted)
            self.assertEqual(SupplyStatus.OFFER_ACCEPTED, supply_offer.supply.status)

    @skip("Currently no info is displayed in acceptation form page")
    def test_clerk_can_access_supply_offer_acceptation_data(self):
        pass

    def test_supply_offer_acceptation_results_in_transport_request(self):
        # given
        self._clerk_tries_to_accept_supply_offer()
        # then
        with self.session_maker() as session:
            supply_transport_request = (
                session.query(SupplyTransportRequest)
                .where(SupplyTransportRequest.supply_id == self.supply_id)
                .one()
            )
            supply_offer = (
                session.query(SupplyOffer)
                .where(SupplyOffer.id == self.supply_offer_id)
                .one()
            )
            self.assertFalse(supply_transport_request.transport_request.accepted)
            self.assertEqual(
                self.price, supply_transport_request.transport_request.transport.price
            )
            self.assertEqual(
                self.transport_request_deadline,
                supply_transport_request.transport_request.request_deadline,
            )
            self.assertEqual(
                supply_offer.source_location_id,
                supply_transport_request.transport_request.transport.pickup_location_id,
            )
            self.assertEqual(
                supply_transport_request.supply.warehouse.location_id,
                supply_transport_request.transport_request.transport.destination_location_id,
            )
            self.assertEqual(
                supply_offer.load_time_window_id,
                supply_transport_request.transport_request.transport.load_time_window_id,
            )
            self.assertEqual(
                supply_transport_request.supply.supply_time_window_id,
                supply_transport_request.transport_request.transport.destination_time_window_id,
            )

    def test_supply_offer_acceptation_results_in_supply_receipt(self):
        # given
        self._clerk_tries_to_accept_supply_offer()

        # then
        with self.session_maker() as session:
            receipt = (
                session.query(SupplyReceipt)
                .where(SupplyReceipt.offer_id == self.supply_offer_id)
                .one()
            )
            self.assertEqual(self.today_datetime, receipt.offer_acceptance_datetime)
            self.assertEqual(self.supply_request_id, receipt.request_id)
            self.assertEqual(self.supply_offer_id, receipt.offer_id)
            self.assertEqual(self.clerk_id, receipt.clerk_id)
