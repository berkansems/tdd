from django.test import SimpleTestCase
from rest_framework.test import APIClient
import requests_mock
import requests
from app import calc


class CalsTests(SimpleTestCase):

    def test_plus(self):
        result = calc.plus(3, 4)
        self.assertEqual(result, 7)

    def test_subtract(self):
        result = calc.subtract(10, 16)
        self.assertEqual(result, 6)

    def test_google(self):
        client = APIClient()
        res = client.get('https://google.com')
        #it normally block outgoing requests to prevent tests from making real requests to external services.
        self.assertEqual(res.status_code, 404)

    def test_google_mocked(self):
        with requests_mock.Mocker() as m:
            m.get('https://google.com', status_code=200)
            response = requests.get('https://google.com')
            self.assertEqual(response.status_code, 200)