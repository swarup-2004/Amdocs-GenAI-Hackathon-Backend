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

    




