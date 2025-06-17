from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Character(models.Model):
    # 필수
    character = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="characters")
    name = models.CharField(max_length=30)

    # 임시 이미지 null=True, blank=True
    character_image = models.ImageField(
        upload_to="character/image/%Y/%m/%d/", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=50)
    intro = models.TextField()

    # 선택
    description = models.TextField(null=True, blank=True)
    character_info = models.TextField(null=True, blank=True)
    example_situation = models.TextField(null=True, blank=True)
    presentation = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.name})"
