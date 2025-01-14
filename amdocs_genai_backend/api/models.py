from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    class UserType(models.TextChoices):
        A = "A", "Insufficient Data"
        B = "B", "Sufficient Data"

    email = models.EmailField(unique=True)
    city = models.CharField(max_length=255)
    college = models.CharField(max_length=255)
    user_type = models.CharField(
        max_length=1,
        choices=UserType.choices,
        default=UserType.A
    )

