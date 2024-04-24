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
from core.models import Ingredient, Recipe
from decimal import Decimal

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

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingedients to those assigned to recipes."""
        in1 = Ingredient.objects.create(user=self.user, name='Apples')
        in2 = Ingredient.objects.create(user=self.user, name='Turkey')
        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )
        recipe.ingredients.add(in1)
        ser1 = IngredientSerializer(in1)
        ser2 = IngredientSerializer(in2)
        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertIn(ser1.data, res.data)
        self.assertNotIn(ser2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered ingredients returns a unique list."""
        in1 = Ingredient.objects.create(user=self.user, name='Apples')
        in2 = Ingredient.objects.create(user=self.user, name='Turkey')
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=Decimal('5.00'),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=Decimal('2.00'),
            user=self.user,
        )
        recipe1.ingredients.add(in1)
        recipe2.ingredients.add(in1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        ser1 = IngredientSerializer(in1)
        self.assertIn(ser1.data, res.data)
