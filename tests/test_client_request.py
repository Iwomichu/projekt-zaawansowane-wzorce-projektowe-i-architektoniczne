from datetime import datetime, time
from decimal import Decimal
from sqlalchemy import select
from tests.fixtures import Fixtures
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import UserRole
from zwpa.model import ClientRequest
from zwpa.model import User
from zwpa.workflows.AddNewClientRequestWorkflow import AddNewClientRequestWorkflow


class UserTestCase(TestCaseWithDatabase):
    def _add_user(self, user: User) -> None:
        with self.session_maker() as session:
            session.add(user)
            session.commit()

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
        AddNewClientRequestWorkflow(self.session_maker, min_days_to_process=1).add_new_client_request(
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

    def test_client_can_modify_details_of_their_own_client_request(self):
        pass

    def test_client_cannot_modify_details_of_not_their_own_client_request(self):
        pass

    def test_client_cannot_modify_details_of_accepted_client_request(self):
        pass

    def test_client_can_browse_own_client_requests(self):
        pass

    def test_clerk_can_browse_all_client_requests(self):
        pass

    def test_clerk_can_accept_a_client_request(self):
        pass

    def test_client_request_acceptance_results_in_new_transport_request(self):
        pass
