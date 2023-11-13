from unittest import TestCase
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from zwpa.user import LOGIN_ATTEMPTS, AuthenticateUserWorkflow, CreateUserWorkflow, User, UserAlreadyExistsException, UserDoesNotExist, UserHasDifferentPassword, UserHasNoLoginAttemptsLeft, metadata


class UserTestCase(TestCase):
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

    def _add_user(self, user: User) -> None:
        with self.session_maker() as session:
            session.add(user)
            session.commit()

    def test_echo(self):
        self._add_user(user=User(login="user", password=b"xxx", login_attempts_left=LOGIN_ATTEMPTS))
        with self.session_maker() as session:
            self.assertIsNotNone(session.scalars(select(User)).one_or_none())

    def test_create_user_happy_path(self):
        # given
        user_login = "user"
        user_password = "password123"
        
        # when
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        # then
        with self.session_maker() as session:
            user = session.scalars(select(User)).one_or_none()
        
        self.assertIsNotNone(user)
        self.assertEqual(user_login, user.login)

    def test_create_user_already_exists(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)
        
        # when / then
        with self.assertRaises(UserAlreadyExistsException):
            CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

    def test_user_can_authenticate(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        # when
        result = AuthenticateUserWorkflow().authenticate_user(login=user_login, plain_text_password=user_password)

        # then
        self.assertTrue(result.authenticated)

    def test_succesful_authentication_resets_login_attempts(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        # when
        result = AuthenticateUserWorkflow().authenticate_user(login=user_login, plain_text_password=user_password)

        # then
        self.assertEqual(result.attempts_left, LOGIN_ATTEMPTS)

    def test_unsuccesful_authentication_for_non_existant_user(self):
        # given
        user_login = "user"
        user_password = "password123"

        # when / then
        with self.assertRaises(UserDoesNotExist):
            AuthenticateUserWorkflow().authenticate_user(login=user_login, plain_text_password=user_password)
        

    def test_unsuccesful_authentication_wrong_password(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        # when / then
        with self.assertRaises(UserHasDifferentPassword) as context:
            AuthenticateUserWorkflow().authenticate_user(login=user_login, plain_text_password="otherpassword")

        self.assertFalse(context.exception.authentication_result.authenticated)

    def test_unsuccesful_authentication_decrements_login_attempts(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        # when / then
        with self.assertRaises(UserHasDifferentPassword):
            AuthenticateUserWorkflow().authenticate_user(login=user_login, plain_text_password="otherpassword")

        with self.session_maker() as session:
            user = session.scalars(select(User).filter_by(login=user_login)).one()

        self.assertEqual(LOGIN_ATTEMPTS - 1, user.login_attempts_left)

    def test_authentication_fails_when_no_login_attempts_left(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        with self.session_maker() as session:
            session.scalars(select(User).filter_by(login=user_login)).one().login_attempts_left = 0
            session.commit()


        # when / then
        with self.assertRaises(UserHasNoLoginAttemptsLeft):
            AuthenticateUserWorkflow().authenticate_user(login=user_login, plain_text_password=user_password)
