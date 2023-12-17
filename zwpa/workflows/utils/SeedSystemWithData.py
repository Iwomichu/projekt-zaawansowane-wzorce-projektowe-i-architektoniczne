from faker import Faker
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import *


class SeedSystemWithDataWorkflow:
    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker
        self.fake = Faker()

    def seed(self) -> None:
        with self.session_maker() as session:
            self.create_users_with_role(session, role=UserRole.CLERK, count=5)
            self.create_users_with_role(session, role=UserRole.CLIENT, count=5)
            self.create_users_with_role(session, role=UserRole.TRANSPORT, count=5)
            self.create_users_with_role(session, role=UserRole.SUPPLIER, count=5)
            self.create_products(session, count=10)
            self.create_warehouses(session, count=20)

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
                label=self.fake.word(),
                unit="ISO_CONTAINER",
            )
            for _ in range(count)
        ]
        session.add_all(products)
        return [product.id for product in products]

    def create_warehouses(self, session: Session, count: int) -> list[int]:
        warehouses = [
            Warehouse(
                label=self.fake.word(),
                location=self.create_location(),
                load_time_windows=[self.create_time_window(), self.create_time_window()]
            )
            for _ in range(count)
        ]
        session.add_all(warehouses)
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
