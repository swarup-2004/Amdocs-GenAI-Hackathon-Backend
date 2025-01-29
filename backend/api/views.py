# views.py
from rest_framework import generics
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status, views
from .serializers import CustomUserCreateSerializer, GoalSerializer
from .models import Goal, Skill
from .utils.is_smart import is_smart_goal
from .utils.preliminary_test_question_generation import generate_test


User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer

class GoalModelViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        # Prepare the serializer with request data
        serializer = self.get_serializer(data=request.data)

        # Validate the serializer data
        serializer.is_valid(raise_exception=True)

        # Check if the goal is a smart goal
        goal_title = serializer.validated_data.get('title')
        goal_description = serializer.validated_data.get('description')
        goal_duration_months = serializer.validated_data.get('duration_months')
        goal_duration_days = serializer.validated_data.get('duration_days')
        skills = Skill.objects.filter(user=request.user).values_list('name', flat=True)
        print(type(skills))
        is_smart_goal_dict = is_smart_goal(goal_title, goal_description, skills, goal_duration_months * 30 + goal_duration_days)

        if is_smart_goal_dict['is_smart'] == 'yes':
            serializer.validated_data['is_smart'] = True
            # Save the instance and explicitly pass the user
            serializer.save(user=request.user)

            # Return the serialized data with a 201 response (created)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Return the response with a 400 status code
            return Response(is_smart_goal_dict, status=status.HTTP_400_BAD_REQUEST)


class PreliminaryQuizAPIView(views.APIView):
    def get(self, request, *args, **kwargs):

        education = request.data.get('education', '')
        goal_title = request.data.get('goal_title', '')
        goal_desc = request.data.get('goal_desc', '')
        skills = Skill.objects.filter(user=request.user).values_list('name', flat=True)
        questions = generate_test(education, goal_title, goal_desc, skills)
        # print(questions)
        return Response(questions, status=status.HTTP_200_OK)
    

