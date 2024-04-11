"""
Test For Models
"""
from decimal import Decimal
from core import models
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch


def create_sample_user(email='em@example.com', password='pss123'):
    return get_user_model().objects.create_user(email, password)


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

    def test_create_recipe(self):
        """test creating recipe successfully"""
        user = get_user_model().objects.create_superuser(email='admin@example.com', password='PASSWORD')
        recipe = models.Recipe.objects.create(
            user=user,
            title='Test Recipe',
            time_minutes=5,
            price=Decimal(5.5),
            description='Test Description'
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = create_sample_user()
        tag = models.Tag.objects.create(user=user, name='Vegan')
        self.assertEqual(str(tag), tag.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""

        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
