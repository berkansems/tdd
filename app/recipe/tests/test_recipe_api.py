from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase
from django.urls import reverse
from core.models import Recipe
from django.contrib.auth import get_user_model
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


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


class PublicRecipeApiTests(TestCase):
    '''Test unauthenticated recipe API access is allowed'''
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''the auth is required to get recipe list'''
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='ber@gmail.com',
            password='<PASSWORD>',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        other_user = get_user_model().objects.create_user(
            email='ali@example.com',
            password='PASSWORD222',
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_detail(self):
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        '''
        Test creating a new recipe
        :return:
        '''
        payload = {'title': 'Sample Recipe',
                   'price': Decimal('15.66'),
                   'link': 'http://example.com'}

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        recipe = create_recipe(user=self.user)
        payload = {'title': 'Updated Title'}
        res = self.client.patch(detail_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])

    def test_full_update(self):

        recipe = create_recipe(user=self.user)
        payload = {'title': 'Updated Title',
                   'description': 'Updated Description',
                   'link': 'http://example.com.tr',
                   'time_minutes': 25,
                   'price': Decimal('32.25'),
                   }

        res = self.client.put(detail_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        new_user = get_user_model().objects.create_user(email='bb@fn.com', password='<PASSWORD>')

        recipe = create_recipe(user=self.user)
        payload = {'user': new_user.id}
        res = self.client.patch(detail_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)
        res = self.client.delete(detail_url(recipe.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 0)

    def test_delete_another_user_recipe(self):
        new_user = get_user_model().objects.create_user(email='alis@gm.com', password='<PASSWORD>')
        new_recipe = create_recipe(user=new_user)
        res = self.client.delete(detail_url(new_recipe.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=new_recipe.id).exists())
