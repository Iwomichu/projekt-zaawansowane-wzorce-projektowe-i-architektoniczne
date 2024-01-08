from datetime import date, datetime, time, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from zwpa.model import (
    ClientRequest,
    Location,
    Product,
    Supply,
    SupplyOffer,
    SupplyRequest,
    SupplyStatus,
    TimeWindow,
    Transport,
    TransportOffer,
    TransportOfferStatus,
    TransportRequest,
    TransportStatus,
    UserRole,
    Warehouse,
    WarehouseProduct,
)
from zwpa.model import UserRoleAssignment

from zwpa.model import User
from zwpa.views.LocationView import LocationView
from zwpa.views.SupplyOfferView import SupplyOfferView
from zwpa.views.SupplyRequestView import SupplyRequestView
from zwpa.views.SupplyView import SupplyView
from zwpa.workflows.client_requests.AddNewClientRequestWorkflow import TodayProvider
from zwpa.workflows.client_requests.GetClientRequestsWorkflow import ClientRequestView
from zwpa.workflows.client_requests.HandleClientRequestAcceptanceFormWorkflow import (
    ClientRequestAcceptanceFormData,
    TimeWindowView,
    WarehouseView,
)
from zwpa.workflows.client_requests.HandleClientRequestFormWorkflow import ProductView
from zwpa.workflows.supplies.HandleSupplyOfferFormWorkflow import (
    SupplyOfferFormInitData,
)
from zwpa.workflows.supplies.HandleSupplyRequestFormWorkflow import (
    SupplyRequestFormData,
)
from zwpa.workflows.transport.ListTransportRequestsWorkflow import TransportRequestView
from zwpa.workflows.transport.ListTransportsWorkflow import CompleteTransportView
from zwpa.workflows.user.ListUserRolesWorkflow import UserRolesView


LONGITUDE = 8.33
LATITUDE = 12.11
LOGIN = "user"
PASSWORD = b"password"
PRODUCT_LABEL = "BOX"
PRODUCT_UNIT = "ISO_CONTAINER"
TIME_WINDOW_START = time(6, 0)
TIME_WINDOW_END = time(15, 0)
PRICE = Decimal(1.0)
TODAY_DATE = date(2020, 1, 1)
REQUEST_DEADLINE = date(2020, 2, 1)
TRANSPORT_DEADLINE = date(2020, 3, 1)
UNIT_COUNT = 1
WAREHOUSE_LABEL = "Test Warehouse"


class Fixtures:
    current_id_counter: int = 0

    @classmethod
    def next_id(cls) -> int:
        cls.current_id_counter += 1
        return cls.current_id_counter

    @classmethod
    def new_user(
        cls,
        session: Session,
        id: int | None = None,
        login: str = LOGIN,
        password: bytes = PASSWORD,
        login_attempts_left: int = 3,
    ) -> User:
        user = User(
            id=id if id is not None else cls.next_id(),
            login=login,
            password=password,
            login_attempts_left=login_attempts_left,
        )
        session.add(user)
        return user

    @classmethod
    def new_user_with_roles(
        cls,
        session: Session,
        roles: list[UserRole],
        id: int | None = None,
        login: str = LOGIN,
        password: bytes = PASSWORD,
        login_attempts_left: int = 3,
    ) -> User:
        if id is None:
            id = cls.next_id()

        user = cls.new_user(
            session,
            id=id,
            login=login,
            password=password,
            login_attempts_left=login_attempts_left,
        )
        for role in roles:
            cls.new_role_assignment(session, user_id=id, role=role)
        return user

    @classmethod
    def new_role_assignment(
        cls,
        session: Session,
        role: UserRole,
        user_id: int,
        id: int | None = None,
    ) -> UserRoleAssignment:
        user_role_assignment = UserRoleAssignment(
            role=role, user_id=user_id, id=id if id is not None else cls.next_id()
        )
        session.add(user_role_assignment)
        return user_role_assignment

    @classmethod
    def new_product(
        cls,
        session: Session,
        id: int | None = None,
        label: str = PRODUCT_LABEL,
        unit: str = PRODUCT_UNIT,
    ) -> Product:
        product = Product(
            id=id if id is not None else cls.next_id(), label=label, unit=unit
        )
        session.add(product)
        return product

    @classmethod
    def new_product_view(
        cls, id: int, label: str = PRODUCT_LABEL, unit: str = PRODUCT_UNIT
    ) -> ProductView:
        return ProductView(id=id, label=label)

    @classmethod
    def new_time_window(
        cls,
        session: Session,
        id: int | None = None,
        start: time = TIME_WINDOW_START,
        end: time = TIME_WINDOW_END,
    ) -> TimeWindow:
        time_window = TimeWindow(
            id=id if id is not None else cls.next_id(), start=start, end=end
        )
        session.add(time_window)
        return time_window

    @classmethod
    def new_location(
        cls,
        session: Session,
        id: int | None = None,
        longitude: float = LONGITUDE,
        latitude: float = LATITUDE,
    ) -> Location:
        location = Location(
            id=id if id is not None else cls.next_id(),
            longitude=longitude,
            latitude=latitude,
        )
        session.add(location)
        return location

    @classmethod
    def new_location_view(cls, location_id: int) -> LocationView:
        return LocationView(id=location_id, longitude=LONGITUDE, latitude=LATITUDE)

    @classmethod
    def new_client_request(
        cls,
        session: Session,
        product_id: int | None = None,
        client_id: int | None = None,
        supply_time_window_id: int | None = None,
        destination_id: int | None = None,
        price: Decimal = PRICE,
        unit_count: int = UNIT_COUNT,
        request_deadline: date = REQUEST_DEADLINE,
        transport_deadline: date = TRANSPORT_DEADLINE,
        accepted: bool = False,
        id: int | None = None,
    ) -> ClientRequest:
        if product_id is None:
            product_id = cls.next_id()
            cls.new_product(session, id=product_id)
        if client_id is None:
            client_id = cls.next_id()
            cls.new_user(session, id=client_id)
        if supply_time_window_id is None:
            supply_time_window_id = cls.next_id()
            cls.new_time_window(session, id=supply_time_window_id)
        if destination_id is None:
            destination_id = cls.next_id()
            cls.new_location(session, id=destination_id)
        client_request = ClientRequest(
            product_id=product_id,
            client_id=client_id,
            supply_time_window_id=supply_time_window_id,
            destination_id=destination_id,
            id=id if id is not None else cls.next_id(),
            price=price,
            unit_count=unit_count,
            request_deadline=request_deadline,
            transport_deadline=transport_deadline,
            accepted=accepted,
        )
        session.add(client_request)
        return client_request

    @classmethod
    def new_client_request_view(
        cls,
        client_id: int,
        id: int | None = None,
        product_name: str = PRODUCT_LABEL,
        product_unit: str = PRODUCT_UNIT,
        destination_longitude: float = LONGITUDE,
        destination_latitude: float = LATITUDE,
        supply_time_window_start: time = TIME_WINDOW_START,
        supply_time_window_end: time = TIME_WINDOW_END,
        price: Decimal = PRICE,
        unit_count: int = UNIT_COUNT,
        request_deadline: date = REQUEST_DEADLINE,
        transport_deadline: date = TRANSPORT_DEADLINE,
        accepted: bool = False,
    ) -> ClientRequestView:
        return ClientRequestView(
            id=id if id is not None else cls.next_id(),
            client_id=client_id,
            product_name=product_name,
            product_unit=product_unit,
            price=price,
            unit_count=unit_count,
            request_deadline=request_deadline,
            transport_deadline=transport_deadline,
            destination_longitude=destination_longitude,
            destination_latitude=destination_latitude,
            supply_time_window_start=supply_time_window_start,
            supply_time_window_end=supply_time_window_end,
            accepted=accepted,
        )

    @classmethod
    def new_warehouse(
        cls,
        session: Session,
        location_id: int | None = None,
        label: str = WAREHOUSE_LABEL,
        load_time_window_id: int | None = None,
        id: int | None = None,
    ) -> Warehouse:
        if location_id is None:
            location_id = cls.next_id()
            cls.new_location(session, id=location_id)

        if load_time_window_id is not None:
            time_window = session.get(TimeWindow, load_time_window_id)
        else:
            time_window = cls.new_time_window(session)

        warehouse = Warehouse(
            id=id if id is not None else cls.next_id(),
            location_id=location_id,
            label=label,
            load_time_windows=[time_window],
        )
        session.add(warehouse)
        return warehouse

    @classmethod
    def new_warehouse_product(
        cls,
        session: Session,
        warehouse_id: int,
        product_id: int,
        current_count: int = UNIT_COUNT,
        id: int | None = None,
    ) -> WarehouseProduct:
        warehouse_product = WarehouseProduct(
            id=id if id is not None else cls.next_id(),
            warehouse_id=warehouse_id,
            product_id=product_id,
            current_count=current_count,
        )
        session.add(warehouse_product)
        return warehouse_product

    @classmethod
    def new_today_provider(
        cls, today: datetime = datetime(2020, 1, 1, tzinfo=timezone.utc)
    ) -> TodayProvider:
        class FakeTodayProvider:
            def today(self) -> datetime:
                return today

        return FakeTodayProvider()

    @classmethod
    def new_user_roles_view(
        cls,
        user_id: int,
        user_login: str = LOGIN,
        is_admin: bool = False,
        is_clerk: bool = False,
        is_client: bool = False,
        is_supplier: bool = False,
        is_transport: bool = False,
    ) -> UserRolesView:
        return UserRolesView(
            id=user_id,
            login=user_login,
            is_admin=is_admin,
            is_clerk=is_clerk,
            is_client=is_client,
            is_supplier=is_supplier,
            is_transport=is_transport,
        )

    @classmethod
    def new_transport(
        cls,
        session: Session,
        unit_count: int = UNIT_COUNT,
        price: Decimal = PRICE,
        status: TransportStatus = TransportStatus.REQUESTED,
        pickup_location_id: int | None = None,
        destination_location_id: int | None = None,
        load_time_window_id: int | None = None,
        destination_time_window_id: int | None = None,
        id: int | None = None,
    ) -> Transport:
        if pickup_location_id is None:
            pickup_location_id = cls.new_location(session).id

        if destination_location_id is None:
            destination_location_id = cls.new_location(session).id

        if load_time_window_id is None:
            load_time_window_id = cls.new_time_window(session).id

        if destination_time_window_id is None:
            destination_time_window_id = cls.new_time_window(session).id

        transport = Transport(
            id=id if id is not None else cls.next_id(),
            unit_count=unit_count,
            price=price,
            pickup_location_id=pickup_location_id,
            destination_location_id=destination_location_id,
            load_time_window_id=load_time_window_id,
            destination_time_window_id=destination_time_window_id,
            status=status,
        )
        session.add(transport)
        return transport

    @classmethod
    def new_transport_request(
        cls,
        session: Session,
        transport_id: int,
        request_deadline: date = REQUEST_DEADLINE,
        id: int | None = None,
    ) -> TransportRequest:
        transport_request = TransportRequest(
            transport_id=transport_id,
            id=id if id is not None else cls.next_id(),
            request_deadline=request_deadline,
        )
        session.add(transport_request)
        return transport_request

    @classmethod
    def new_transport_request_view(
        cls,
        request_id: int,
        unit_count: int = UNIT_COUNT,
        price: Decimal = PRICE,
        pickup_location_longitude: float = LONGITUDE,
        pickup_location_latitude: float = LATITUDE,
        destination_location_longitude: float = LONGITUDE,
        destination_location_latitude: float = LATITUDE,
        load_time_window_start: time = TIME_WINDOW_START,
        load_time_window_end: time = TIME_WINDOW_END,
        destination_time_window_start: time = TIME_WINDOW_START,
        destination_time_window_end: time = TIME_WINDOW_END,
        request_deadline: date = REQUEST_DEADLINE,
        user_already_made_offer_on_the_request=False,
    ) -> TransportRequestView:
        return TransportRequestView(
            request_id=request_id,
            unit_count=unit_count,
            price=price,
            pickup_location_longitude=pickup_location_longitude,
            pickup_location_latitude=pickup_location_latitude,
            destination_location_longitude=destination_location_longitude,
            destination_location_latitude=destination_location_latitude,
            load_time_window_start=load_time_window_start,
            load_time_window_end=load_time_window_end,
            destination_time_window_start=destination_time_window_start,
            destination_time_window_end=destination_time_window_end,
            request_deadline=request_deadline,
            user_already_made_offer_on_the_request=user_already_made_offer_on_the_request,
        )

    @classmethod
    def new_complete_transport_view(
        cls,
        transport_id: int,
        unit_count: int = UNIT_COUNT,
        price: Decimal = PRICE,
        pickup_location_longitude: float = LONGITUDE,
        pickup_location_latitude: float = LATITUDE,
        destination_location_longitude: float = LONGITUDE,
        destination_location_latitude: float = LATITUDE,
        load_time_window_start: time = TIME_WINDOW_START,
        load_time_window_end: time = TIME_WINDOW_END,
        destination_time_window_start: time = TIME_WINDOW_START,
        destination_time_window_end: time = TIME_WINDOW_END,
        status: TransportStatus = TransportStatus.REQUESTED,
        transporter_id: int | None = None,
        transporter_login: str | None = None,
    ) -> CompleteTransportView:
        return CompleteTransportView(
            unit_count=unit_count,
            price=price,
            pickup_location_longitude=pickup_location_longitude,
            pickup_location_latitude=pickup_location_latitude,
            destination_location_longitude=destination_location_longitude,
            destination_location_latitude=destination_location_latitude,
            load_time_window_start=load_time_window_start,
            load_time_window_end=load_time_window_end,
            destination_time_window_start=destination_time_window_start,
            destination_time_window_end=destination_time_window_end,
            id=transport_id,
            status=status,
            transporter_id=transporter_id,
            transporter_login=transporter_login,
        )

    @classmethod
    def new_transport_offer(
        cls,
        session: Session,
        transport_id: int,
        transporter_id: int,
        status: TransportOfferStatus = TransportOfferStatus.PENDING,
        id: int | None = None,
    ) -> TransportOffer:
        offer = TransportOffer(
            id=id if id is not None else cls.next_id(),
            transport_id=transport_id,
            transporter_id=transporter_id,
            status=status,
        )
        session.add(offer)
        return offer

    @classmethod
    def new_time_window_view(cls, time_window_id: int) -> TimeWindowView:
        return TimeWindowView(
            id=time_window_id, start=TIME_WINDOW_START, end=TIME_WINDOW_END
        )

    @classmethod
    def new_warehouse_view(
        cls, warehouse_id: int, time_window_id: int
    ) -> WarehouseView:
        return WarehouseView(
            id=warehouse_id,
            label=WAREHOUSE_LABEL,
            load_time_windows=[cls.new_time_window_view(time_window_id)],
        )

    @classmethod
    def new_client_request_acceptance_form_data(
        cls,
        client_id: int,
        client_request_id: int,
        warehouse_id: int,
        time_window_id: int,
    ) -> ClientRequestAcceptanceFormData:
        client_request = cls.new_client_request_view(
            id=client_request_id, client_id=client_id
        )
        warehouse = cls.new_warehouse_view(warehouse_id, time_window_id=time_window_id)
        return ClientRequestAcceptanceFormData(
            client_request=client_request, warehouses=[warehouse]
        )

    @classmethod
    def new_supply(
        cls,
        session: Session,
        unit_count: int = UNIT_COUNT,
        status: SupplyStatus = SupplyStatus.REQUESTED,
        id: int | None = None,
        product_id: int | None = None,
        warehouse_id: int | None = None,
        supply_time_window_id: int | None = None,
    ) -> Supply:
        if product_id is None:
            product_id = cls.next_id()
            cls.new_product(session, id=product_id)

        if supply_time_window_id is None:
            supply_time_window_id = cls.next_id()
            cls.new_time_window(session, id=supply_time_window_id)

        if warehouse_id is None:
            warehouse_id = cls.next_id()
            cls.new_warehouse(
                session, id=warehouse_id, load_time_window_id=supply_time_window_id
            )

        supply = Supply(
            unit_count=unit_count,
            status=status,
            id=id if id is not None else cls.next_id(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            supply_time_window_id=supply_time_window_id,
        )
        session.add(supply)
        return supply

    @classmethod
    def new_supply_view(
        cls,
        supply_id: int,
        product_id: int,
        warehouse_id: int,
        time_window_id: int,
        status: SupplyStatus = SupplyStatus.REQUESTED,
        unit_count: int = UNIT_COUNT,
    ) -> SupplyView:
        return SupplyView(
            id=supply_id,
            status=status,
            unit_count=unit_count,
            product=cls.new_product_view(product_id),
            warehouse=cls.new_warehouse_view(warehouse_id, time_window_id),
        )

    @classmethod
    def new_supply_request_view(
        cls,
        supply_request_id: int,
        supply_id: int,
        product_id: int,
        warehouse_id: int,
        time_window_id: int,
        request_deadline: date = REQUEST_DEADLINE,
    ) -> SupplyRequestView:
        return SupplyRequestView(
            id=supply_request_id,
            supply=cls.new_supply_view(
                supply_id=supply_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                time_window_id=time_window_id,
            ),
            request_deadline=request_deadline,
        )

    @classmethod
    def new_supply_request(
        cls,
        session: Session,
        request_deadline: date = REQUEST_DEADLINE,
        id: int | None = None,
        supply_id: int | None = None,
        clerk_id: int | None = None,
    ) -> SupplyRequest:
        if supply_id is None:
            supply_id = cls.next_id()
            cls.new_supply(session, id=supply_id)
        if clerk_id is None:
            clerk_id = cls.next_id()
            cls.new_user_with_roles(session, id=clerk_id, roles=[UserRole.CLERK])

        supply_request = SupplyRequest(
            request_deadline=request_deadline,
            id=id if id is not None else cls.next_id(),
            supply_id=supply_id,
            clerk_id=clerk_id,
        )
        session.add(supply_request)
        return supply_request

    @classmethod
    def new_supply_request_form_data(
        cls, warehouse_id: int, time_window_id: int, product_ids: list[int]
    ) -> SupplyRequestFormData:
        return SupplyRequestFormData(
            warehouses=[cls.new_warehouse_view(warehouse_id, time_window_id)],
            products=[
                Fixtures.new_product_view(product_id) for product_id in product_ids
            ],
        )

    @classmethod
    def new_supply_offer_form_data(
        cls,
        supply_request_id: int,
        supply_id: int,
        warehouse_id: int,
        time_window_id: int,
        product_id: int,
    ) -> SupplyOfferFormInitData:
        return SupplyOfferFormInitData(
            supply_request=Fixtures.new_supply_request_view(
                supply_request_id=supply_request_id,
                supply_id=supply_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                time_window_id=time_window_id,
            )
        )

    @classmethod
    def new_supply_offer(
        cls,
        session: Session,
        price: Decimal = PRICE,
        transport_deadline: date = TRANSPORT_DEADLINE,
        accepted: bool = False,
        id: int | None = None,
        supplier_id: int | None = None,
        supply_id: int | None = None,
        load_time_window_id: int | None = None,
        source_location_id: int | None = None,
    ) -> SupplyOffer:
        if supplier_id is None:
            supplier_id = cls.new_user_with_roles(session, roles=[UserRole.SUPPLIER]).id

        if supply_id is None:
            supply_id = cls.new_supply(session).id

        if load_time_window_id is None:
            load_time_window_id = cls.new_time_window(session).id

        if source_location_id is None:
            source_location_id = cls.new_location(session).id

        supply_offer = SupplyOffer(
            id=id if id is not None else cls.next_id(),
            price=price,
            transport_deadline=transport_deadline,
            supply_id=supply_id,
            supplier_id=supplier_id,
            load_time_window_id=load_time_window_id,
            source_location_id=source_location_id,
            accepted=accepted,
        )
        session.add(supply_offer)
        return supply_offer

    @classmethod
    def new_supply_offer_view(
        cls,
        supply_offer_id: int,
        supply_id: int,
        load_time_window_id: int,
        source_location_id: int,
        product_id: int,
        warehouse_id: int,
        destination_window_id: int,
    ) -> SupplyOfferView:
        return SupplyOfferView(
            accepted=False,
            price=PRICE,
            transport_deadline=TRANSPORT_DEADLINE,
            id=supply_offer_id,
            supply=cls.new_supply_view(
                supply_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                time_window_id=destination_window_id,
            ),
            load_time_window=cls.new_time_window_view(load_time_window_id),
            supplier_login=LOGIN,
            source_location=cls.new_location_view(source_location_id),
        )
