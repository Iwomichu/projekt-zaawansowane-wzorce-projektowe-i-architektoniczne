from decimal import Decimal
from unittest import skip
from sqlalchemy import select
from tests.fixtures import UNIT_COUNT, Fixtures
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import ClientTransportRequest, UserRole, WarehouseProduct
from zwpa.model import ClientRequest
from zwpa.workflows.client_requests.AcceptClientRequestWorkflow import (
    AcceptClientRequestWorkflow,
    ChosenWarehouseDoesNotSatisfyNeededCount,
    RequestAlreadyAccepted,
)
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import (
    AddNewClientRequestWorkflow,
)
from zwpa.workflows.client_requests.GetClientRequestsWorkflow import (
    GetClientRequestsWorkflow,
)
from zwpa.workflows.client_requests.HandleClientRequestAcceptanceFormWorkflow import (
    HandleClientRequestAcceptanceFormWorkflow,
)


class ClientRequestTestCase(TestCaseWithDatabase):
    def test_client_can_create_client_request(self):
        # given
        with self.session_maker(expire_on_commit=False) as session:
            user = Fixtures.new_user(session)
            product = Fixtures.new_product(session)
            Fixtures.new_role_assignment(session, role=UserRole.CLIENT, user_id=user.id)
            expected_destination = Fixtures.new_location(session)
            expected_supply_time_window = Fixtures.new_time_window(session)
            session.commit()
            expected_client_request = Fixtures.new_client_request(
                session=session,
                product_id=product.id,
                client_id=user.id,
                destination_id=expected_destination.id,
                supply_time_window_id=expected_supply_time_window.id,
            )
            session.commit()

        # when
        AddNewClientRequestWorkflow(
            self.session_maker,
            min_days_to_process=1,
            today_provider=Fixtures.new_today_provider(),
        ).add_new_client_request(
            user_id=user.id,
            price=expected_client_request.price,
            unit_count=expected_client_request.unit_count,
            request_deadline=expected_client_request.request_deadline,
            transport_deadline=expected_client_request.transport_deadline,
            product_id=expected_client_request.product_id,
            supply_time_window=(
                expected_supply_time_window.start,
                expected_supply_time_window.end,
            ),
            destination=(
                expected_destination.longitude,
                expected_destination.latitude,
            ),
        )
        # then
        with self.session_maker(expire_on_commit=False) as session:
            result_client_request = session.scalars(
                select(ClientRequest).filter(
                    ClientRequest.id != expected_client_request.id
                )
            ).one_or_none()

            self.assertIsNotNone(result_client_request)
            self.assertEqual(expected_client_request.product_id, result_client_request.product_id)  # type: ignore
            self.assertEqual(expected_client_request.client_id, result_client_request.client_id)  # type: ignore
            self.assertEqual(expected_supply_time_window.start, result_client_request.supply_time_window.start)  # type: ignore
            self.assertEqual(expected_supply_time_window.end, result_client_request.supply_time_window.end)  # type: ignore
            self.assertEqual(expected_destination.longitude, result_client_request.destination.longitude)  # type: ignore
            self.assertEqual(expected_destination.latitude, result_client_request.destination.latitude)  # type: ignore
            self.assertEqual(expected_client_request.price, result_client_request.price)  # type: ignore
            self.assertEqual(expected_client_request.unit_count, result_client_request.unit_count)  # type: ignore
            self.assertEqual(expected_client_request.request_deadline, result_client_request.request_deadline)  # type: ignore
            self.assertEqual(expected_client_request.transport_deadline, result_client_request.transport_deadline)  # type: ignore
            self.assertEqual(expected_client_request.accepted, result_client_request.accepted)  # type: ignore

    @skip(reason="nonprio")
    def test_client_can_modify_details_of_their_own_client_request(self):
        pass

    @skip(reason="nonprio")
    def test_client_cannot_modify_details_of_not_their_own_client_request(self):
        pass

    @skip(reason="nonprio")
    def test_client_cannot_modify_details_of_accepted_client_request(self):
        pass

    def test_client_can_browse_own_client_requests(self):
        # given
        with self.session_maker(expire_on_commit=False) as session:
            this_user = Fixtures.new_user(session)
            other_user = Fixtures.new_user(session)
            product = Fixtures.new_product(session)
            Fixtures.new_role_assignment(
                session, role=UserRole.CLIENT, user_id=this_user.id
            )
            expected_destination = Fixtures.new_location(session)
            expected_supply_time_window = Fixtures.new_time_window(session)
            session.commit()
            this_client_request = Fixtures.new_client_request(
                session=session,
                product_id=product.id,
                client_id=this_user.id,
                destination_id=expected_destination.id,
                supply_time_window_id=expected_supply_time_window.id,
            )
            Fixtures.new_client_request(
                session=session,
                product_id=product.id,
                client_id=other_user.id,
                destination_id=expected_destination.id,
                supply_time_window_id=expected_supply_time_window.id,
            )
            session.commit()
        expected_views = [
            Fixtures.new_client_request_view(
                id=this_client_request.id, client_id=this_user.id
            )
        ]

        # when
        result_views = GetClientRequestsWorkflow(
            self.session_maker
        ).get_my_client_requests_workflow(this_user.id)

        # then
        self.assertCountEqual(expected_views, result_views)

    def test_clerk_can_browse_all_client_requests(self):
        # given
        with self.session_maker(expire_on_commit=False) as session:
            clerk = Fixtures.new_user(session)
            client_1 = Fixtures.new_user(session)
            client_2 = Fixtures.new_user(session)
            product = Fixtures.new_product(session)
            Fixtures.new_role_assignment(session, role=UserRole.CLERK, user_id=clerk.id)
            expected_destination = Fixtures.new_location(session)
            expected_supply_time_window = Fixtures.new_time_window(session)
            session.commit()
            client_1_request = Fixtures.new_client_request(
                session=session,
                product_id=product.id,
                client_id=client_1.id,
                destination_id=expected_destination.id,
                supply_time_window_id=expected_supply_time_window.id,
            )
            client_2_request = Fixtures.new_client_request(
                session=session,
                product_id=product.id,
                client_id=client_2.id,
                destination_id=expected_destination.id,
                supply_time_window_id=expected_supply_time_window.id,
            )
            session.commit()
        expected_views = [
            Fixtures.new_client_request_view(
                id=client_1_request.id, client_id=client_1.id
            ),
            Fixtures.new_client_request_view(
                id=client_2_request.id, client_id=client_2.id
            ),
        ]

        # when
        result_views = GetClientRequestsWorkflow(
            self.session_maker
        ).get_all_client_requests_workflow(clerk.id)

        # then
        self.assertCountEqual(expected_views, result_views)

    def test_clerk_can_access_client_request_acceptance_form(self):
        # given
        with self.session_maker() as session:
            client_id = Fixtures.new_user_with_roles(
                session, roles=[UserRole.CLIENT]
            ).id
            client_request = Fixtures.new_client_request(
                session, client_id=client_id
            )
            client_request_id = client_request.id
            warehouse = Fixtures.new_warehouse(session)
            warehouse_id = warehouse.id
            Fixtures.new_warehouse_product(
                session, warehouse_id=warehouse_id, product_id=client_request.product_id
            )
            time_window_id = warehouse.load_time_windows[0].id
            clerk_id = Fixtures.new_user_with_roles(session, roles=[UserRole.CLERK]).id
            session.commit()

        workflow = HandleClientRequestAcceptanceFormWorkflow(self.session_maker)
        # when
        result = workflow.get_form_data(clerk_id, client_request_id)
        expected = Fixtures.new_client_request_acceptance_form_data(
            client_id=client_id,
            client_request_id=client_request_id,
            warehouse_id=warehouse_id,
            time_window_id=time_window_id,
        )
        # then
        self.assertEqual(result, expected)

    def test_client_request_acceptance_form_only_shows_warehouses_that_satisfy_the_count_requirement(
        self,
    ):
        # given
        with self.session_maker() as session:
            client_id = Fixtures.new_user_with_roles(
                session, roles=[UserRole.CLIENT]
            ).id
            client_request = Fixtures.new_client_request(session, client_id=client_id)
            client_request_id = client_request.id
            warehouse = Fixtures.new_warehouse(session)
            Fixtures.new_warehouse(session)
            warehouse_id = warehouse.id
            time_window_id = warehouse.load_time_windows[0].id
            clerk_id = Fixtures.new_user_with_roles(session, roles=[UserRole.CLERK]).id
            Fixtures.new_warehouse_product(
                session, warehouse_id=warehouse_id, product_id=client_request.product_id
            )
            session.commit()

        workflow = HandleClientRequestAcceptanceFormWorkflow(self.session_maker)
        # when
        result = workflow.get_form_data(clerk_id, client_request_id)
        expected = Fixtures.new_client_request_acceptance_form_data(
            client_id=client_id,
            client_request_id=client_request_id,
            warehouse_id=warehouse_id,
            time_window_id=time_window_id,
        )
        # then
        self.assertEqual(result, expected)


class ClientRequestAcceptingTestCase(TestCaseWithDatabase):
    def _prepare_fixtures(self):
        today_provider = Fixtures.new_today_provider()
        with self.session_maker(expire_on_commit=False) as session:
            clerk = Fixtures.new_user(session)
            Fixtures.new_role_assignment(session, role=UserRole.CLERK, user_id=clerk.id)
            warehouse = Fixtures.new_warehouse(session)
            product = Fixtures.new_product(session)
            warehouse_product = Fixtures.new_warehouse_product(
                session, warehouse_id=warehouse.id, product_id=product.id
            )
            client_request = Fixtures.new_client_request(
                session=session, product_id=product.id
            )
            load_time_window = Fixtures.new_time_window(session)
            session.commit()
        return (
            today_provider,
            clerk,
            warehouse,
            client_request,
            load_time_window,
            warehouse_product,
        )

    def test_clerk_can_accept_a_client_request(self):
        # given
        (
            today_provider,
            clerk,
            warehouse,
            client_request,
            load_time_window,
            warehouse_product,
        ) = self._prepare_fixtures()

        # when
        AcceptClientRequestWorkflow(
            self.session_maker,
            today_provider=today_provider,
        ).accept_client_request(
            user_id=clerk.id,
            client_request_id=client_request.id,
            warehouse_id=warehouse.id,
            transport_request_deadline=client_request.request_deadline,
            time_window_id=load_time_window.id,
            price_for_transport=Decimal(1.00),
        )

        # then
        with self.session_maker() as session:
            result_client_request = session.get_one(ClientRequest, client_request.id)
            self.assertTrue(result_client_request.accepted)

    def test_accepting_client_request_creates_new_transport_request(self):
        # given
        (
            today_provider,
            clerk,
            warehouse,
            client_request,
            load_time_window,
            warehouse_product,
        ) = self._prepare_fixtures()
        # when
        AcceptClientRequestWorkflow(
            self.session_maker,
            today_provider=today_provider,
        ).accept_client_request(
            user_id=clerk.id,
            client_request_id=client_request.id,
            warehouse_id=warehouse.id,
            transport_request_deadline=client_request.request_deadline,
            time_window_id=load_time_window.id,
            price_for_transport=Decimal(1.00),
        )

        # then
        with self.session_maker() as session:
            client_transport_request = session.execute(
                select(ClientTransportRequest)
            ).scalar_one()
            transport_request = client_transport_request.transport_request
            transport = transport_request.transport
            self.assertEqual(
                client_request.destination_id, transport.destination_location_id
            )
            self.assertEqual(
                client_request.supply_time_window_id,
                transport.destination_time_window_id,
            )
            self.assertEqual(load_time_window.id, transport.load_time_window_id)
            self.assertEqual(warehouse.location_id, transport.pickup_location_id)
            self.assertEqual(client_request.unit_count, transport.unit_count)
            self.assertEqual(
                client_request.request_deadline, transport_request.request_deadline
            )
            self.assertEqual(Decimal(1.00), transport.price)

    def test_accepting_client_request_reduces_product_count_at_warehouse(self):
        # given
        (
            today_provider,
            clerk,
            warehouse,
            client_request,
            load_time_window,
            warehouse_product,
        ) = self._prepare_fixtures()
        # when
        AcceptClientRequestWorkflow(
            self.session_maker,
            today_provider=today_provider,
        ).accept_client_request(
            user_id=clerk.id,
            client_request_id=client_request.id,
            warehouse_id=warehouse.id,
            transport_request_deadline=client_request.request_deadline,
            time_window_id=load_time_window.id,
            price_for_transport=Decimal(1.00),
        )

        # then
        with self.session_maker() as session:
            session.add(warehouse_product)
            session.refresh(warehouse_product)
            self.assertEqual(warehouse_product.current_count, 0)

    def test_accepting_client_request_fails_if_product_unavailable(self):
        # given
        (
            today_provider,
            clerk,
            warehouse,
            client_request,
            load_time_window,
            warehouse_product,
        ) = self._prepare_fixtures()
        with self.session_maker() as session:
            session.add(client_request)
            client_request.unit_count = UNIT_COUNT + 1
            session.commit()

            # when / then
            self.assertRaises(
                ChosenWarehouseDoesNotSatisfyNeededCount,
                AcceptClientRequestWorkflow(
                    self.session_maker,
                    today_provider=today_provider,
                ).accept_client_request,
                user_id=clerk.id,
                client_request_id=client_request.id,
                warehouse_id=warehouse.id,
                transport_request_deadline=client_request.request_deadline,
                time_window_id=load_time_window.id,
                price_for_transport=Decimal(1.00),
            )

    def test_accepting_client_request_fails_if_request_already_accepted(self):
        # given
        (
            today_provider,
            clerk,
            warehouse,
            client_request,
            load_time_window,
            warehouse_product,
        ) = self._prepare_fixtures()

        with self.session_maker() as session:
            session.add(client_request)
            client_request.accepted = True
            session.commit()

            # when / then
            self.assertRaises(
                RequestAlreadyAccepted,
                AcceptClientRequestWorkflow(
                    self.session_maker,
                    today_provider=today_provider,
                ).accept_client_request,
                user_id=clerk.id,
                client_request_id=client_request.id,
                warehouse_id=warehouse.id,
                transport_request_deadline=client_request.request_deadline,
                time_window_id=load_time_window.id,
                price_for_transport=Decimal(1.00),
            )
