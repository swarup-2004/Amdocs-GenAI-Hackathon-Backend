# views.py
from rest_framework import generics
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status, views
from .serializers import CustomUserCreateSerializer, GoalSerializer, TestSerializer, FeedbackSerializer, ScoreSerializer
from .models import Goal, Skill, Test, Score, Feedback, LearningModule
from .utils.is_smart import is_smart_goal
from .utils.preliminary_test_question_generation import generate_test
from .utils.qdrant_utils import insert_point 


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
        # Get data from request
        education = request.data.get('education', '')
        goal_title = request.data.get('goal_title', '')
        goal_desc = request.data.get('goal_desc', '')

        # Fetch skills related to the user
        skills = Skill.objects.filter(user=request.user).values_list('name', flat=True)

        # Generate questions based on the provided details
        questions = generate_test(education, goal_title, goal_desc, skills)

        # Insert the generated questions into Qdrant or wherever needed
        qdrant_id = insert_point("tests", questions)

        # Create the TestSerializer instance with user and qdrant_id
        test_serializer = TestSerializer(data={'user': request.user.id, 'qdrant_id': qdrant_id})

        if test_serializer.is_valid():
            # Save the serialized data to the database
            test_serializer.save()

            # Return response with the serialized data and generated questions
            return Response({
                "data": test_serializer.data,
                "questions": questions
            }, status=status.HTTP_200_OK)
        else:
            return Response(test_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class LearningModuleAPIView(views.APIView):
    # def post(self, request, *args, **kwargs):
    #     # Get the data from the request
    #     goal_id = request.data.get('goal_id', '')
    #     qdrant_id = request.data.get('qdrant_id', '')

    #     # Create the LearningModule instance
    #     learning_module = LearningModule.objects.create(
    #         user=request.user,
    #         goal_id=goal_id,
    #         qdrant_id=qdrant_id
    #     )

    #     # Return the response with the serialized data
    #     return Response({
    #         "data": {
    #             "user": learning_module.user.id,
    #             "goal": learning_module.goal_id,
    #             "qdrant_id": learning_module.qdrant_id
    #         }
    #     }, status=status.HTTP_200_OK)

    pass 

class FeedbackModelViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer

    def get_queryset(self):
        return Feedback.objects.filter(user=self.request.user)
    
class ScoreModelViewSet(viewsets.ModelViewSet):
    serializer_class = ScoreSerializer

    def get_queryset(self):
        return Score.objects.filter(user=self.request.user)