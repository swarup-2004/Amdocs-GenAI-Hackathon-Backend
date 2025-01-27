from django.contrib import admin
from .models import CustomUser, Goal

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Goal)