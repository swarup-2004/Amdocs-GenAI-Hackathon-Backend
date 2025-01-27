from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model
from .models import Goal

User = get_user_model()

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'linkedin_url', 'github_url', 'leetcode_url', 'city', 'college')  
        extra_kwargs = {
            'first_name': {'required': True},
            'email': {'required': True, 'allow_blank': False, 'validators': []}, 
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    

# Custom serializer for retrieving/updating user details
class CustomUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'linkedin_url', 'github_url', 'leetcode_url', 'city', 'college') 


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = "__all__"
        extra_kwargs = {
            'is_smart': {'required': False},
            'user': {'required': False}
        }




