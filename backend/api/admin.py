from django.contrib import admin
from .models import CustomUser, Goal, Skill, Test, Score, Feedback, LearningModule

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Goal)
admin.site.register(Skill)
admin.site.register(Test)
admin.site.register(Score)
admin.site.register(Feedback)
admin.site.register(LearningModule)