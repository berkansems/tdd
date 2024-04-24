"""
Views for the recipe APIs
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from core.models import Recipe, Tag, Ingredient
from recipe import serializers

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter write like 1,2,3',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter',
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_id_list(self, objs):
        return [int(obj) for obj in objs.split(',') ]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        tags = self.request.query_params.get('tags', None)
        ingredients = self.request.query_params.get('ingredients', None)
        queryset = self.queryset
        if tags is not None:
            queryset = queryset.filter(tags__id__in=self._get_id_list(tags))
        if ingredients is not None:
            queryset = queryset.filter(ingredients__id__in=self._get_id_list(ingredients))
        return queryset.filter(user=self.request.user).order_by('-id').distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.RecipeSerializer
        if self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT,
                enum=[0, 1],
                description='Filter by items assigned to recipes.',
            ),
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        assigned_only = bool(self.request.query_params.get('assigned_only', 0))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipes__isnull=False)

        return queryset.filter(user=self.request.user).order_by('-name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    '''
    if we directly inherit from viewsets.ModelViewSet it handles tag-detail endpoint also  because it
    has inheritet from :
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    classes but now we inherit from viewsets.GenericViewSet
    '''
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
