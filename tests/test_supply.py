from tests.fixtures import Fixtures, REQUEST_DEADLINE, UNIT_COUNT
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import SupplyRequest, SupplyStatus, UserRole
from zwpa.workflows.supplies.CreateNewSupplyRequestWorkflow import (
    CreateNewSupplyRequestWorkflow,
)
from zwpa.workflows.supplies.HandleSupplyOfferFormWorkflow import (
    HandleSupplyOfferFormWorkflow,
)
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

    def test_supplier_can_access_supply_offer_creation_data(self):
        # given
        workflow = HandleSupplyOfferFormWorkflow(self.session_maker)
        with self.session_maker() as session:
            supplier_id = Fixtures.new_user_with_roles(session, roles=[UserRole.SUPPLIER]).id
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
        result = workflow.get_form_data(supplier_id, supply_request_id=supply_request_id)
        
        # then
        self.assertEqual(expected, result)

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
