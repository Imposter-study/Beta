from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random

class User(AbstractUser):
    GENDER_CHOICES = [("M", "남자"), ("F", "여자"), ("O", "기타")]
    WORD_POOL = [
        "red", "blue", "yellow", "purple", "green",
        "dog", "bird", "monkey", "tiger", "cow"
    ]

    username = models.CharField(max_length=20, unique=True)
    nickname = models.CharField(max_length=20, unique=True)
    gender = models.CharField(default="O", choices=GENDER_CHOICES, max_length=1)
    birth_date = models.DateField(null=True, blank=True)
    introduce = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )

    # follower = models.ManyToManyField(
    #    "self", symmetrical=False, related_name="following", blank=True
    # )
    def save(self, *args, **kwargs):  # 자동 닉네임 생성 추가
        if not self.nickname:
            self.nickname = self.generate_random_nickname()
        super().save(*args, **kwargs)

    def generate_random_nickname(self):  # 랜덤 닉네임 생성기
        while True:
            nickname = (
                f"{random.choice(self.WORD_POOL)}_"
                f"{random.choice(self.WORD_POOL)}_"
                f"{random.randint(100, 999)}"
            )
            if not User.objects.filter(nickname=nickname).exists():
                return nickname

    def mark_as_deactivated(self):
        self.is_active = False
        self.save()

    def is_ready_for_deletion(self):
        if self.is_deactivated and self.deactivated_at:
            return timezone.now() >= self.deactivated_at + timedelta(days=90)
        return False

    def __str__(self):
        return self.username
