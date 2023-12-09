from zwpa.model import metadata


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer


from unittest import TestCase


class TestCaseWithDatabase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.postgres = PostgresContainer("postgres:11")
        cls.postgres.start()
        cls.engine = create_engine(cls.postgres.get_connection_url())
        cls.session_maker = sessionmaker(cls.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.postgres.stop()

    def setUp(self) -> None:
        with self.engine.begin() as connection:
            metadata.create_all(connection)

    @classmethod
    def cleanup_database(cls) -> None:
        with cls.engine.begin() as connection:
            for table in reversed(metadata.sorted_tables):
                connection.execute(table.delete())

    def tearDown(self) -> None:
        self.cleanup_database()