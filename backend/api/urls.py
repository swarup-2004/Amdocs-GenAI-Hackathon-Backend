# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import GoalModelViewSet

router = DefaultRouter()
router.register(r'goals', GoalModelViewSet, basename='goals')

urlpatterns = [
    path('', include(router.urls)),
]
