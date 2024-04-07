'''
serializers for user api view.
'''

from django.contrib.auth import (get_user_model, authenticate)

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    '''Serializers for user object'''

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        '''create and return with encrypted data'''
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    '''Serializers for user object'''
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attr):
        email = attr.get('email')
        password = attr.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = 'unable to authenticate with provided credentials'
            raise serializers.ValidationError(msg, code='authorization')
        attr['user'] = user
        return attr

    def create(self, validated_data):
        '''create and return with encrypted data'''
        return get_user_model().objects.create_user(**validated_data)
