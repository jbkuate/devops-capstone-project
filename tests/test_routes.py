"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    ################################################################################
    # ADD YOUR TEST CASES HERE ...
    ################################################################################
    def test_get_account_list(self):
        """It should Get a list of Accounts"""
        self._create_accounts(5)
        # send a self.client.get() request to the BASE_URL
        resp = self.client.get(BASE_URL)
        # assert that the resp.status_code is status.HTTP_200_OK
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # get the data from resp.get_json()
        data = resp.get_json()
        # assert that the len() of the data is 5 (the number of accounts you created)
        self.assertEqual(len(data), 5)

    def test_read_an_account(self):
        """It should Get a single Account"""

        # Make a self.client.post() call to accounts to create a new account,
        # passing in some account data.
        account = AccountFactory()
        resp = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        # assert that the resp.status_code is status.HTTP_201_CREATED
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Get back the account id that was generated from the json
        new_account = resp.get_json()
        account_id = new_account["id"]
        # Make a self.client.get() call to /accounts/{id} passing in that account id.
        resp = self.client.get(f"{BASE_URL}/{account_id}")
        # assert that the resp.status_code is status.HTTP_200_OK
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Check the json that was returned
        data = resp.get_json()
        # assert that it is equal to the data that you sent.
        self.assertEqual(data["name"], new_account["name"])
        self.assertEqual(data["email"], new_account["email"])
        self.assertEqual(data["address"], new_account["address"])
        self.assertEqual(data.get("phone_number"), new_account.get("phone_number"))
        self.assertEqual(data.get("date_joined"), new_account.get("date_joined"))

    def test_account_not_found(self):
        """It should not Get a Account thats not found"""

        # Make a self.client.get() call to /accounts/{id} passing in 0 as the account id
        response = self.client.get(f"{BASE_URL}/0")
        # Assert that the return code was HTTP_404_NOT_FOUND.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("was not found", data["message"])

    #################################################################
    #   Update a account
    #################################################################
    def test_update_account(self):
        """It should Update an existing account"""
        # create a account to update
        test_account = AccountFactory()
        # send a self.client.post() request to the BASE_URL with a json payload of test_account.serialize()
        response = self.client.post(f"{BASE_URL}", json=test_account.serialize())
        # assert that the resp.status_code is status.HTTP_201_CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # UPDATE THE account
        # get the data from resp.get_json() as new_account
        new_account = response.get_json()
        # change new_account["description"] to unknown
        new_account["email"] = "bosco@kumadef.com"
        # send a self.client.put() request to the BASE_URL with a json payload of new_account
        response = self.client.put(f"{BASE_URL}/{new_account['id']}", json=new_account)
        # assert that the resp.status_code is status.HTTP_200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get the data from resp.get_json() as updated_account
        updated_account = response.get_json()
        # assert that the updated_account["description"] is whatever you changed it to
        self.assertEqual(updated_account["email"], "bosco@kumadef.com")

    def test_update_account_not_found(self):
        """It should not Update an unexisting account"""
        # create a account to update
        test_account = AccountFactory()
        # send a self.client.post() request to the BASE_URL with a json payload of test_account.serialize()
        response = self.client.post(f"{BASE_URL}", json=test_account.serialize())
        # assert that the resp.status_code is status.HTTP_201_CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # UPDATE THE account
        # get the data from resp.get_json() as new_account
        new_account = response.get_json()
        # change new_account["description"] to unknown
        new_account["email"] = "bosco@kumadef.com"
        # send a self.client.put() request to the BASE_URL with a json payload of new_account
        response = self.client.put(f"{BASE_URL}/0", json=new_account)
        # assert that the resp.status_code is status.HTTP_404_NOT_FOUND
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # get the data from resp.get_json() as updated_account
        data = response.get_json()
        self.assertIn("was not found", data["message"])

    #################################################################
    #   Delete a account
    #################################################################
    def test_delete_account(self):
        """It should Delete a account"""

        # create a list accounts containing 5 accounts using the _create_accounts() method.
        accounts = self._create_accounts(5)
        # call the self.get_account_count() method to retrieve the initial count of accounts before any deletion
        original_count = self.get_account_count()
        # assign the first account from the accounts list to the variable test_account
        test_account = accounts[0]
        # send a self.client.delete() request to the BASE_URL with test_account.id
        response = self.client.delete(f"{BASE_URL}/{test_account.id}")
        # assert that the resp.status_code is status.HTTP_204_NO_CONTENT
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # check if the response data is empty
        self.assertTrue(len(response.data) == 0)
        # send a self.client.get request to the same endpoint that was deleted to retrieve the deteled account
        response = self.client.get(f"{BASE_URL}/{test_account.id}")
        # assert that the resp.status_code is status.HTTP_404_NOT_FOUND to confirm deletion of the account
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # retrieve the count of accounts after the deletion operation
        current_count = self.get_account_count()
        # check if the new count of accounts is one less than the initial count
        self.assertTrue(current_count < original_count)

    #################################################################
    #   Security tests case
    #################################################################

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    def test_cors_security(self):
        """It should return a CORS header"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check for the CORS header
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')

    ######################################################################
    # Utility functions
    ######################################################################

    def get_account_count(self):
        """save the current number of accounts"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
