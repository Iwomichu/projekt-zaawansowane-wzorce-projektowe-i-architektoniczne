from tests.fixtures import Fixtures
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import UserRole
from zwpa.workflows.supplies.HandleSupplyRequestFormWorkflow import (
    HandleSupplyRequestFormWorkflow,
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
        pass

    def test_supplier_can_access_supply_offer_creation_data(self):
        pass

    def test_supplier_can_create_supply_offer(self):
        pass

    def test_clerk_can_access_supply_request_acceptation_data(self):
        pass

    def test_clerk_can_accept_supply_offer(self):
        pass

    def test_supply_offer_acceptation_results_in_transport_request(self):
        pass

    def test_supply_offer_acceptation_results_in_supply_receipt(self):
        pass
