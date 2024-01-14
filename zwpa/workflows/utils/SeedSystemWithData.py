from datetime import timedelta
from decimal import Decimal
import random
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import *


START_DATE = datetime.today()
EXAMPLE_PRODUCTS = list({
    "Smartphone",
    "Laptop",
    "Tablet",
    "Digital Camera",
    "Headphones",
    "Bluetooth Speaker",
    "Smartwatch",
    "Fitness Tracker",
    "Desktop Computer",
    "Gaming Console",
    "E-reader",
    "External Hard Drive",
    "USB Flash Drive",
    "Wireless Mouse",
    "Mechanical Keyboard",
    "Printer",
    "Monitor",
    "Projector",
    "GPS Navigation System",
    "Smart Home Hub",
    "Action Camera",
    "Drones",
    "Virtual Reality Headset",
    "Wireless Router",
    "Portable Charger",
    "Wireless Earbuds",
    "Digital Voice Recorder",
    "CCTV Camera",
    "External SSD",
    "Graphics Card",
    "Computer Speakers",
    "Microphone",
    "Webcam",
    "Network Switch",
    "Solar Charger",
    "Noise-Canceling Headphones",
    "Fitness Smart Scale",
    "Blu-ray Player",
    "Digital Drawing Tablet",
    "Wireless Charging Pad",
    "Digital Thermometer",
    "Power Strip",
    "HDMI Cable",
    "VR Gaming Controller",
    "Smart Doorbell",
    "Car GPS",
    "Smart Lighting Kit",
    "Solar-Powered Calculator",
})


class SeedSystemWithDataWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker
        self.fake = Faker()

    def seed(self) -> None:
        with self.session_maker() as session:
            if self._is_system_seeded_already(session):
                print("System is seeded already. Seeding aborted.")
                return

            self.create_users_with_role(session, role=UserRole.CLERK, count=5)
            client_ids = self.create_users_with_role(
                session, role=UserRole.CLIENT, count=5
            )
            self.create_users_with_role(session, role=UserRole.TRANSPORT, count=5)
            self.create_users_with_role(session, role=UserRole.SUPPLIER, count=5)
            product_ids = self.create_products(session, count=30)
            self.create_warehouses(session, count=20, product_ids=product_ids)
            self.create_client_requests(
                session, count=10, client_ids=client_ids, product_ids=product_ids
            )

    def _is_system_seeded_already(self, session: Session) -> bool:
        return session.execute(select(Product)).first() is not None

    def create_time_window(self) -> TimeWindow:
        return TimeWindow(
            start=time(0, 0),
            end=self.fake.time_object(),
        )

    def create_location(self) -> Location:
        return Location(
            label=self.fake.street_address(),
            longitude=float(self.fake.coordinate()),
            latitude=float(self.fake.coordinate()),
        )

    def create_products(self, session: Session, count: int) -> list[int]:
        products = [
            Product(
                label=label,
                unit="ISO_CONTAINER",
                retail_price=Decimal(random.random() * (10 ** random.randint(0, 4))),
            )
            for label in random.sample(EXAMPLE_PRODUCTS, k=count)
        ]
        session.add_all(products)
        session.commit()
        return [product.id for product in products]

    def create_warehouses(
        self, session: Session, count: int, product_ids: list[int]
    ) -> list[int]:
        warehouses = [
            Warehouse(
                label=self.fake.word(),
                location=self.create_location(),
                load_time_windows=[
                    self.create_time_window(),
                    self.create_time_window(),
                ],
            )
            for _ in range(count)
        ]
        warehouse_products = [
            WarehouseProduct(
                warehouse=warehouse,
                product_id=product_id,
                current_count=random.randint(0, 30),
            )
            for warehouse in warehouses
            for product_id in random.sample(product_ids, k=random.randint(3, 12))
        ]
        session.add_all(warehouses)
        session.add_all(warehouse_products)
        session.commit()
        return [warehouse.id for warehouse in warehouses]

    def create_users(self, session: Session, count: int) -> list[int]:
        users = [
            User(
                login=self.fake.last_name(),
                password=self.fake.binary(length=32),
                login_attempts_left=3,
            )
            for _ in range(count)
        ]
        session.add_all(users)
        session.commit()
        return [user.id for user in users]

    def create_users_with_role(
        self, session: Session, count: int, role: UserRole
    ) -> list[int]:
        user_ids = self.create_users(session, count=count)
        role_assignments = [
            UserRoleAssignment(role=role, user_id=user_id) for user_id in user_ids
        ]
        session.add_all(role_assignments)
        session.commit()
        return user_ids

    def create_client_requests(
        self,
        session: Session,
        count: int,
        client_ids: list[int],
        product_ids: list[int],
    ) -> list[int]:
        clients = list(
            session.execute(select(User).where(User.id.in_(client_ids))).scalars()
        )
        products = list(
            session.execute(
                select(Product).where(Product.id.in_(product_ids))
            ).scalars()
        )
        requests = []
        for _ in range(count):
            client = random.choice(clients)
            product = random.choice(products)
            location = self.create_location()
            time_window = self.create_time_window()
            request = ClientRequest(
                price=Decimal(random.randint(1, 100)),
                unit_count=random.randint(1, 10),
                request_deadline=self.fake.date_between(
                    START_DATE, START_DATE + timedelta(days=60)
                ),
                transport_deadline=self.fake.date_between(
                    START_DATE + timedelta(days=30), START_DATE + timedelta(days=90)
                ),
                accepted=False,
                product=product,
                client=client,
                destination=location,
                supply_time_window=time_window,
            )
            requests.append(request)
        session.add_all(requests)
        session.commit()
        return [request.id for request in requests]
