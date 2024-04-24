from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase
from django.urls import reverse
from core.models import Recipe, Ingredient, Tag
from django.contrib.auth import get_user_model
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer, IngredientSerializer
import tempfile
import os

from PIL import Image


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return an image upload URL."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_existing_of_ingredients(self):
        recipe = create_recipe(user=self.user)
        ingredient_1 = Ingredient.objects.create(user=self.user, name='Kale')
        ingredient_2 = Ingredient.objects.create(user=self.user, name='Salt')
        recipe.ingredients.add(ingredient_1, ingredient_2)
        serializer = IngredientSerializer(Ingredient.objects.all().order_by('name'), many=True)
        res = self.client.get(detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['ingredients']), 2)
        self.assertEqual(res.data['title'], 'Sample Recipe')
        self.assertEqual(res.data['ingredients'], serializer.data)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with new ingredients."""
        payload = {
            'title': 'Cauliflower Tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
        }
        recipe = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(recipe.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(len(recipes), 1)

        user_recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(len(user_recipes), 1)
        self.assertEqual(user_recipes[0].ingredients.count(), 2)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertEqual(len(ingredients), 2)
        self.assertEqual(ingredients[0].user, self.user)

        for ingredient in payload['ingredients']:
            self.assertTrue(
                Ingredient.objects.filter(name=ingredient['name']).exists()
            )

    def test_create_recipe_with_existing_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user, name='Salt')
        payload = {
            'title': 'Cauliflower Tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertEqual(len(ingredients), 2)
        self. assertIn(ingredient, ingredients)

    def test_update_recipe_ingredients(self):
        payload = {
            'title': 'Cauliflower Tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        payload = {'ingredients': [{'name': 'sut'}]}
        res = self.client.patch(detail_url(recipe.id), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.count(), len(payload['ingredients']))
        self.assertEqual(recipe.ingredients.values('name')[0]['name'], payload['ingredients'][0]['name'])

    def test_clear_recipe_ingredients(self):
        payload = {
            'title': 'Cauliflower Tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        payload = {'ingredients': []}
        res = self.client.patch(detail_url(recipe.id), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """test filter recipe by tags."""
        r1 = Recipe.objects.create(user=self.user, title='Salt', price=2.33)
        r2 = Recipe.objects.create(user=self.user, title='Sut', price=23.33)
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Meat')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = Recipe.objects.create(user=self.user, title='Paa', price=10.00)

        res = self.client.get(RECIPES_URL, {'tags': f'{tag1.id}, {tag2.id}'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """test filter recipe by tags."""
        r1 = Recipe.objects.create(user=self.user, title='Salt', price=2.33)
        r2 = Recipe.objects.create(user=self.user, title='Sut', price=23.33)
        ingredient1 = Ingredient.objects.create(user=self.user, name='Vegan')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Meat')
        r1.ingredients.add(ingredient1)
        r2.ingredients.add(ingredient2)
        r3 = Recipe.objects.create(user=self.user, title='Paa', price=10.00)

        res = self.client.get(RECIPES_URL, {'ingredients': f'{ingredient1.id},{ingredient2.id}'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        '''
        Clean up after each test it is run opposite to setup
        :return:
        '''
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
