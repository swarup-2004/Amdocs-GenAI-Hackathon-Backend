# Generated by Django 5.1.1 on 2025-02-02 04:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0016_test_module_info"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="github_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="leetcode_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="linkedin_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="test",
            name="module_info",
            field=models.CharField(default="", max_length=255),
        ),
    ]
