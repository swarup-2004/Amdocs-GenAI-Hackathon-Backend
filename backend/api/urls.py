# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import GoalModelViewSet, ScoreModelViewSet, FeedbackModelViewSet, LearningModuleAPIView, TestModelViewSet


router = DefaultRouter()
router.register(r'goals', GoalModelViewSet, basename='goals')
router.register(r'scores', ScoreModelViewSet, basename='scores')
router.register(r'feedback', FeedbackModelViewSet, basename='feedback')
router.register(r'tests', TestModelViewSet, basename='tests')

urlpatterns = [
    path('', include(router.urls)),
    path('learning-modules/', LearningModuleAPIView.as_view(), name='modules')
]
