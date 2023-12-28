from tests.fixtures import Fixtures
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import TransportStatus, UserRole
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
