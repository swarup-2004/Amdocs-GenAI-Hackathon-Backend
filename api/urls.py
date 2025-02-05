# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import GoalModelViewSet, ScoreModelViewSet, FeedbackModelViewSet, LearningModuleModelViewSet, TestModelViewSet, CourseRecommendationAPIView


router = DefaultRouter()
router.register(r'goals', GoalModelViewSet, basename='goals')
router.register(r'scores', ScoreModelViewSet, basename='scores')
router.register(r'feedback', FeedbackModelViewSet, basename='feedback')
router.register(r'tests', TestModelViewSet, basename='tests')
router.register(r'learning-modules', LearningModuleModelViewSet, basename='learning-modules')

urlpatterns = [
    path('', include(router.urls)),
    path('recommendations/', CourseRecommendationAPIView.as_view(), name='recommendations'),
]
