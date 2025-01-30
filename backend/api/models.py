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
    linkedin_url = models.URLField()
    github_url = models.URLField()
    leetcode_url = models.URLField()
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
    qdrant_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    def __str__(self):
        return self.qdrant_id
    
class Score(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    right_fluency = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    wrong_fluency = models.DecimalField(max_digits=5, decimal_places=2, default=0) 
    test_id = models.ForeignKey(Test, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.user.username
    

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

    




