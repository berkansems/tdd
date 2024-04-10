'''
for testing the Tag api endpoints
'''
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer
from decimal import Decimal

TAGS_URL = reverse('recipe:tag-list')
RECIPES_URL = reverse('recipe:recipe-list')


def tag_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


def recipe_url(recipe_id):

    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_user(email='test@example.com', password='<PASSWORD>'):
    '''create a test user'''
    return get_user_model().objects.create_user(email=email, password=password)


def create_recipe(**params):

    default = {
        'title': 'Sample Recipe',
        'time_minutes': 22,
        'price': Decimal(5.25),
        'description': 'Sample Recipe Description',
        'link': 'http://example.com',
    }

    default.update(params)

    return Recipe.objects.create(**default)


def create_tag(user, tag_name):

    return Tag.objects.create(user=user, name=tag_name)


class PublicTagTestApi(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagTestApi(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_tags(self):
        create_tag(self.user, 'test1')
        create_tag(self.user, 'test2')
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        user2 = get_user_model().objects.create_user(email='ali@gm.com', password='<PASSWORD>')
        create_tag(self.user, 'test1')
        create_tag(self.user, 'test2')
        create_tag(user2, 'test3')
        tags = Tag.objects.filter(user=self.user).order_by('-name')
        self.assertEqual(tags.count(), 2)
        self.assertEqual(self.user, tags[0].user)
        tags_list = self.client.get(TAGS_URL)
        self.assertEqual(tags_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(tags_list.data), 2)

    def test_tag_get_single_object(self):
        tag = create_tag(self.user, 'test1')
        res = self.client.get(tag_url(tag.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()

    def test_tag_update(self):
        tag = create_tag(self.user, 'test1')
        res = self.client.patch(tag_url(tag.id), {'name': 'new name'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, 'new name')

    def test_delete_tag(self):

        tag = create_tag(self.user, 'test1')
        res = self.client.delete(tag_url(tag.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(id=tag.id)
        self.assertEqual(tags.count(), 0)
        self.assertFalse(tags.exists())

    def test_nested_tags_for_recipe(self):
        tag1 = create_tag(self.user, 'test1')
        tag2 = create_tag(self.user, 'test2')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1, tag2)

        self.assertIn(tag1, recipe.tags.all())
        self.assertIn(tag2, recipe.tags.all())
        res = self.client.get(recipe_url(recipe.id))
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['tags']), 2)

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test create tag when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Lunch'}]}
        url = recipe_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = recipe_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())
        breakfast_exists = Tag.objects.filter(name='Breakfast').exists()
        # this section just tests whether or not tag itself removed from db
        self.assertTrue(breakfast_exists)

    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = recipe_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
