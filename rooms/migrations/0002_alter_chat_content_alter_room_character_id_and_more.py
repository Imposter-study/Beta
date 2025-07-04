# Generated by Django 5.1.7 on 2025-06-30 10:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("characters", "0008_merge_20250629_1545"),
        ("rooms", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="chat",
            name="content",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="room",
            name="character_id",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="characters.character"
            ),
        ),
        migrations.AlterField(
            model_name="room",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
