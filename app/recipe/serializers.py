from rest_framework import serializers
from core.models import (
    Recipe,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'price', 'link', 'time_minutes', 'tags']
        read_only_fields = ['id']

    def _generate_tags(self, instance, tags, user):
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=user,
                **tag,
            )
            instance.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a recipe."""
        tags = self.context['request'].data.get('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context['request'].user
        self._generate_tags(recipe, tags, auth_user)

        return recipe

    def update(self, instance, validated_data):
        tags = self.context['request'].data.get('tags', None)

        if tags is not None:
            # if tags be like empty list it will clear tags
            # removes all previous tags that was in relation with recipe
            instance.tags.clear()
            self._generate_tags(instance, tags, instance.user)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance



class RecipeDetailSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
