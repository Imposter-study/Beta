# Generated by Django 5.1.7 on 2025-06-14 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_alter_user_age_alter_user_gender"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="age",
        ),
        migrations.AddField(
            model_name="user",
            name="birth_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
