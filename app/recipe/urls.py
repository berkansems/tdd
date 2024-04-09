"""
URL mappings for the recipe app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from recipe import views


router = DefaultRouter()
# /api/recipe/recipes/ by setting the below prefix url endpoint will be like this
'''
views.RecipeViewSet automatically set names to urls
for example to retrieve all recipes it set recipe-list
for put patch update it set name to recipe-detail
'''
router.register('recipes', views.RecipeViewSet)
router.register('tags', views.TagViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
