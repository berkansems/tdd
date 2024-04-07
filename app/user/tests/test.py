'''
to test user model
'''
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_new_user(**prarams):
    return get_user_model().objects.create_user(**prarams)


class UserModelTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'email': 'example@example.com',
            'password': 'PASSWORD',
            'name': 'ali',
        }

    def test_create_user(self):
        res = self.client.post(CREATE_USER_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=self.payload['email'])
        self.assertEqual(res.data['email'], user.email)
        self.assertTrue(user.check_password(self.payload['password']))

    def test_user_exists(self):
        create_new_user(**self.payload)
        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        self.payload['password'] = 'ws'
        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(email=self.payload['email']).exists()
        self.assertFalse(user_exist)

    def test_user_token(self):
        self.client.post(CREATE_USER_URL, self.payload)
        res = self.client.post(TOKEN_URL, {
            'email': self.payload['email'],
            'password': self.payload['password']
        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_wrong_password(self):
        self.client.post(CREATE_USER_URL, self.payload)
        res = self.client.post(TOKEN_URL, {
            'email': self.payload['email'],
            'password': 'wrongpass'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_empty_password(self):
        res = self.client.post(TOKEN_URL, {
            'email': self.payload['email'],
            'password': ''
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_retrieve_unuthenticated_user(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):

    def setUp(self):
        self.user = create_new_user(
            email='example@example.com',
            password='pass123',
            name='example'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_user_retrieve(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': 'example',
            'email': 'example@example.com'
        })

    def test_post_user(self):
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user(self):
        payload = {'name': 'ali', 'password': 'newpass'}
        res = self.client.patch(ME_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertTrue(res.status_code, status.HTTP_200_OK)
