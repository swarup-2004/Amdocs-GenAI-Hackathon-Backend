# Generated by Django 5.1.1 on 2025-02-01 06:25

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0013_test_goal_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="test",
            name="goal_id",
        ),
    ]
