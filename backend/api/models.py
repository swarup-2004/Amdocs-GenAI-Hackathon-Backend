from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

# Create your models here.

class CustomUser(AbstractUser):
    class UserType(models.TextChoices):
        A = "A", "Insufficient Data"
        B = "B", "Sufficient Data"
    email = models.EmailField(unique=True)  # Ensure email is unique
    # profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True) 
    city = models.CharField(max_length=255)
    college = models.CharField(max_length=255)
    linkedin_url = models.URLField(null=True, blank=True)
    github_url = models.URLField(null=True, blank=True)
    leetcode_url = models.URLField(null=True, blank=True)
    user_type = models.CharField(
        max_length=1,
        choices=UserType.choices,
        default=UserType.A
    )
    # Override the groups field
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # Unique related name
        blank=True,
    )

    # Override the user_permissions field
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # Unique related name
        blank=True,
    )
    def __str__(self):
        return self.username
    

class Goal(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    duration_months = models.IntegerField(verbose_name='Duration in months', default=0)
    duration_days = models.IntegerField(verbose_name='Duration in days', default=0)
    is_smart = models.BooleanField()
    is_completed = models.BooleanField(default=False)
    def __str__(self):
        return self.title
    
class Skill(models.Model):
    name = models.CharField(max_length=255)
    user = models.ManyToManyField(CustomUser, related_name='skills')
    def __str__(self):
        return self.name
    
class Test(models.Model):
    class TestType(models.TextChoices):
        A = "A", "Preliminary Test"
        B = "B", "Module Test"
    qdrant_id = models.CharField(max_length=255)
    goal_id = models.ForeignKey(Goal, on_delete=models.CASCADE, null=True, blank=True)
    module_info = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_attempted = models.BooleanField(default=False)
    type_of_quiz = models.CharField(max_length=1,
        choices=TestType.choices,
        default=TestType.A)
    def __str__(self):
        return self.module_info
    
class Score(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    right_fluency = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    wrong_fluency = models.DecimalField(max_digits=5, decimal_places=2, default=0) 
    test_id = models.ForeignKey(Test, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.test_id.module_info
    

class LearningModule(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    qdrant_id = models.CharField(max_length=255)
    

class Feedback(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    learning_module = models.ForeignKey(LearningModule, on_delete=models.CASCADE, default=None)
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.user.username

    




