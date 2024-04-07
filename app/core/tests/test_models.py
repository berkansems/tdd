"""
Test For Models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = 'berkan@example.com'
        password = 'test111'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)

    def test_new_user_email_normalized(self):
        sample_emails = [
            ['test1@example.com', 'test1@example.com'],
            ['test2@Example.com', 'test2@example.com'],
            ['test3@EXAMPLE.com', 'test3@example.com'],
            ['Test4@example.com', 'Test4@example.com'],
            ['TEST5@example.com', 'TEST5@example.com'],
        ]
        # note that Test4@example.com and  TEST5@example.com with capital letters at first part is acceptable
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, password='test123')

            self.assertEqual(user.email, expected)

    def test_new_user_invalid_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')

    def test_create_new_superuser(self):
        user = get_user_model().objects.create_superuser(email='admin@example.com', password='PASSWORD')
        self.assertTrue(user.is_superuser, True)
        self.assertTrue(user.is_staff, True)
