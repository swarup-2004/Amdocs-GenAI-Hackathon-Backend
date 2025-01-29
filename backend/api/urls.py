# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import GoalModelViewSet, PreliminaryQuizAPIView, ScoreModelViewSet, FeedbackModelViewSet


router = DefaultRouter()
router.register(r'goals', GoalModelViewSet, basename='goals')
router.register(r'scores', ScoreModelViewSet, basename='scores')
router.register(r'feedback', FeedbackModelViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),
    path('preliminary-quiz/', PreliminaryQuizAPIView.as_view(), name='quiz'),
]
