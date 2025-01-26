# views.py
from rest_framework import generics
from django.contrib.auth import get_user_model
from .serializers import CustomUserCreateSerializer

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer

    

