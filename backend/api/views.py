# views.py
from rest_framework import generics
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status, views
from django.shortcuts import get_object_or_404
from .serializers import CustomUserCreateSerializer, GoalSerializer, TestSerializer, FeedbackSerializer, ScoreSerializer, LearningModuleSerializer
from .models import Goal, Skill, Test, Score, Feedback, LearningModule
from .utils.is_smart import is_smart_goal
from .utils.preliminary_test_question_generation import generate_test
from .utils.qdrant_utils import insert_point, search_point
from .utils.learning_cell_generation import call_chain
from .utils.update_learning_cell import update_learning_module


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
        # print(type(skills))
        is_smart_goal_dict = is_smart_goal(goal_title, goal_description, skills, goal_duration_months * 30 + goal_duration_days)
        # print(is_smart_goal_dict['is_smart'])
        if is_smart_goal_dict['is_smart'].lower() == 'yes':
            serializer.validated_data['is_smart'] = True
            # Save the instance and explicitly pass the user
            serializer.save(user=request.user)

            # Return the serialized data with a 201 response (created)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Return the response with a 400 status code
            return Response(is_smart_goal_dict, status=status.HTTP_400_BAD_REQUEST)

class LearningModuleModelViewSet(viewsets.ModelViewSet):
    serializer_class = LearningModuleSerializer

    def get_queryset(self):
        return LearningModule.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Get the data from the request
        goal_id = request.data.get('goal_id', '')
        learning_module = LearningModule.objects.filter(user=request.user, goal_id=goal_id)
        if learning_module.exists():
            return Response({
                "is_created": True,
                "message": "Learning Module already exists for this goal"
            }, status=status.HTTP_200_OK)
        print(goal_id)  
        goal_title = Goal.objects.get(id=goal_id).title
        education = request.data.get('education', '')
        goal_desc = Goal.objects.get(id=goal_id).description
        skills = Skill.objects.filter(user=request.user).values_list('name', flat=True)
        time_period = Goal.objects.get(id=goal_id).duration_months * 30 + Goal.objects.get(id=goal_id).duration_days
        roadmap, practice = call_chain(education, skills, time_period, goal_title, goal_desc)
        print(roadmap)
        print(practice)
        # print(quiz)
        qdrant_id = insert_point('learning_module', {"roadmap": roadmap, "practice": practice})
        print(qdrant_id)
        # Create the LearningModule instance
        learning_module = LearningModule.objects.create(
            user=request.user,
            goal_id=goal_id,
            qdrant_id=qdrant_id
        )

        # # Return the response with the serialized data
        return Response({
            "data": {
                "user": learning_module.user.id,
                "goal": learning_module.goal_id,
                "qdrant_id": learning_module.qdrant_id
            }
        }, status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        goal_id = request.data.get('goal_id', '')
        if goal_id:
            learning_module = LearningModule.objects.filter(goal_id=goal_id).first()
            data = search_point("learning_module", learning_module.qdrant_id)
            return Response(data, status=status.HTTP_200_OK)
        return super().list(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        id = kwargs.get('pk')
        if id:
            learning_module = LearningModule.objects.get(id=id)
            test = Test.objects.filter(goal_id=learning_module.goal.pk).order_by('-created_at').first()
            feedback = Feedback.objects.filter(learning_module=learning_module.pk).order_by('-created_at').first()
            qdrant_id = learning_module.qdrant_id
            score = Score.objects.filter(test_id=test.pk).order_by('-created_at').first()
            roadmap = search_point("learning_module", qdrant_id).get('roadmap', '')
            practice = search_point("learning_module", qdrant_id).get('practice', '')
            roadmap, practice = update_learning_module(learning_module, test, feedback, score, roadmap=roadmap, practice=practice)
            data = {
                "roadmap": roadmap,
                "practice": practice
            }
            new_qdrant_id = insert_point("learning_module", data)
            learning_module.qdrant_id = new_qdrant_id
            learning_module.save()
            return Response({
                "message": "Learning Module updated successfully"
            }, status=status.HTTP_200_OK)
        return super().partial_update(request, *args, **kwargs)


    

class FeedbackModelViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer

    def get_queryset(self):
        return Feedback.objects.filter(user=self.request.user)
    
class ScoreModelViewSet(viewsets.ModelViewSet):
    serializer_class = ScoreSerializer

    def get_queryset(self):
        return Score.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        # Get the data from the request
        print('here')
        # print(self.request.data)
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        serializer.save(user=request.user)
        print(serializer.validated_data['test_id'])
        test = Test.objects.get(id=serializer.validated_data['test_id'].id)
        test.is_attempted = True
        test.save()
        return Response(
            serializer.data
        , status=status.HTTP_201_CREATED)
    
class TestModelViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer

    def get_queryset(self):
        return Test.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        # Get the instance of the Test
        instance = self.get_object()
        data = search_point("tests", instance.qdrant_id)
        return Response(data, status=status.HTTP_200_OK)
    
    # def list(self, request, *args, **kwargs):
    #     test_id = request.data.get('test_id', '')  # Use query_params for GET requests
    #     print(test_id)

    #     if test_id:
    #         test = get_object_or_404(Test, id=test_id)  # Handles DoesNotExist automatically
    #         data = search_point("tests", test.qdrant_id)
    #         return Response(data, status=status.HTTP_200_OK)

    #     # Ensure the response from the parent method is returned
    #     return super().list(request, *args, **kwargs)
        
    
    def create(self, request, *args, **kwargs):
        # print("here")
        # print(request.data)
        goal_id = request.data.get('goal_id', '')
        education = request.data.get('education', '')
        goal_title = Goal.objects.get(id=goal_id).title
        goal_desc = Goal.objects.get(id=goal_id).description
        type_of_quiz = request.data.get('type_of_quiz', 'B')
        module_info = request.data.get('module_info', '')

        if type_of_quiz == 'A':
            preliminary_quiz = Test.objects.filter(type_of_quiz='A', goal_id=goal_id).first()
            if preliminary_quiz:
                return Response({
                    "data": {
                        "id": preliminary_quiz.id,
                        "is_attempted": preliminary_quiz.is_attempted,
                        "message": "Preliminary test already exists for this goal",
                        "questions": search_point("tests", preliminary_quiz.qdrant_id)
                    }
                }, status=status.HTTP_200_OK)

        # Fetch skills related to the user
        skills = Skill.objects.filter(user=request.user).values_list('name', flat=True)

        # Generate questions based on the provided details
        questions = generate_test(education, goal_title, goal_desc, skills, type_of_quiz, module_info)

        # Insert the generated questions into Qdrant or wherever needed
        qdrant_id = insert_point("tests", questions)

        # Create the TestSerializer instance with user and qdrant_id
        test_serializer = TestSerializer(data={
            'user': request.user.id, 
            'qdrant_id': qdrant_id,
            'goal_id': goal_id,
            'type_of_quiz': type_of_quiz,
            'module_info': module_info
            })

        if test_serializer.is_valid():
            # Save the serialized data to the database
            test_serializer.save(user=request.user)

            # Return response with the serialized data and generated questions
            return Response({
                "data": test_serializer.data,
                "questions": questions
            }, status=status.HTTP_200_OK)
        else:
            return Response(test_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
        
    
