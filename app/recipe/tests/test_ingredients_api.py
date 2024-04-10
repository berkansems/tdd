'''
for testing the Ingredient api endpoints
i write the crate update delete of Ingredient in test_recipe_api
because we practically do this action there
'''
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag, Recipe, Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')

def ingredient_detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_ingredient(user, **params):
    return Ingredient.objects.create(user=user, **params)

class PublicIngredientApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientApiTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(email='berkan>@example.com', password='<PASSWORD>')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient_list(self):
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])
        create_ingredient(self.user, name='Salt')
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], 'Salt')

    def test_retrieve_ingredient_limit_for_user(self):
        new_user = get_user_model().objects.create_user(email='test@ex.com', password='<PASSWORD>')
        create_ingredient(new_user, name='Melo')
        create_ingredient(self.user, name='Ab')
        create_ingredient(self.user, name='Salt')

        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        # checks the ordering of ingredients which is defined by name
        self.assertEqual(res.data[0]['name'], 'Salt')

    def test_ingredient_serializer(self):
        Ingredient.objects.create(user=self.user, name='Salt')
        Ingredient.objects.create(user=self.user, name='Badem')
        # order by is important to pass the test
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_update(self):
        ingredient = Ingredient.objects.create(user=self.user, name='Salt')
        payload = {'name': 'Badem'}
        url = ingredient_detail_url(ingredient.id)
        res = self.client.patch(url, payload)
        ingredient.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], payload['name'])
        self.assertEqual(ingredient.name, payload['name'])

    def test_ingredient_delete(self):
        ingredient = create_ingredient(self.user, name='Salt')
        res = self.client.delete(ingredient_detail_url(ingredient.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(Ingredient.objects.all()), 0)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
