# Generated by Django 5.1.1 on 2025-02-01 06:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0012_test_is_attempted_test_type_of_quiz"),
    ]

    operations = [
        migrations.AddField(
            model_name="test",
            name="goal_id",
            field=models.ForeignKey(
                default=None, on_delete=django.db.models.deletion.CASCADE, to="api.goal"
            ),
        ),
    ]
