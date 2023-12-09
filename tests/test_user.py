from sqlalchemy import select
from tests.test_case_with_database import TestCaseWithDatabase
from zwpa.model import User
from zwpa.workflows.AuthenticateUserWorkflow import AuthenticateUserWorkflow
from zwpa.workflows.CreateUserWorkflow import CreateUserWorkflow
from zwpa.exceptions.UserAlreadyExistsException import UserAlreadyExistsException
from zwpa.exceptions.UserDoesNotExist import UserDoesNotExist
from zwpa.exceptions.UserHasDifferentPassword import UserHasDifferentPassword
from zwpa.exceptions.UserHasNoLoginAttemptsLeft import UserHasNoLoginAttemptsLeft

from zwpa.model import LOGIN_ATTEMPTS


class UserTestCase(TestCaseWithDatabase):
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
        self.assertEqual(user_login, user.login)  # type: ignore // typecheck cannot understand above assertion

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
        result = AuthenticateUserWorkflow(session_maker=self.session_maker).authenticate_user(login=user_login, plain_text_password=user_password)

        # then
        self.assertTrue(result.authenticated)

    def test_succesful_authentication_resets_login_attempts(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        # when
        AuthenticateUserWorkflow(session_maker=self.session_maker).authenticate_user(login=user_login, plain_text_password=user_password)

        # then
        with self.session_maker() as session:
            user = session.scalars(select(User).filter_by(login=user_login)).one()
        self.assertEqual(user.login_attempts_left, LOGIN_ATTEMPTS)

    def test_unsuccesful_authentication_for_non_existant_user(self):
        # given
        user_login = "user"
        user_password = "password123"

        # when / then
        with self.assertRaises(UserDoesNotExist):
            AuthenticateUserWorkflow(session_maker=self.session_maker).authenticate_user(login=user_login, plain_text_password=user_password)
        

    def test_unsuccesful_authentication_wrong_password(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        # when / then
        with self.assertRaises(UserHasDifferentPassword) as context:
            AuthenticateUserWorkflow(session_maker=self.session_maker).authenticate_user(login=user_login, plain_text_password="otherpassword")

        self.assertFalse(context.exception.authentication_result.authenticated)

    def test_unsuccesful_authentication_decrements_login_attempts(self):
        # given
        user_login = "user"
        user_password = "password123"
        CreateUserWorkflow(session_maker=self.session_maker).create_user(login=user_login, plain_text_password=user_password)

        # when / then
        with self.assertRaises(UserHasDifferentPassword):
            AuthenticateUserWorkflow(session_maker=self.session_maker).authenticate_user(login=user_login, plain_text_password="otherpassword")

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
            AuthenticateUserWorkflow(session_maker=self.session_maker).authenticate_user(login=user_login, plain_text_password=user_password)
