from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random, uuid
from django.conf import settings


class User(AbstractUser):
    GENDER_CHOICES = [("M", "남자"), ("F", "여자"), ("O", "기타")]
    WORD_POOL = [
        "red",
        "blue",
        "yellow",
        "purple",
        "green",
        "dog",
        "bird",
        "monkey",
        "tiger",
        "cow",
    ]
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=20, unique=True)
    nickname = models.CharField(max_length=30, unique=True, blank=True, null=True)
    gender = models.CharField(default="O", choices=GENDER_CHOICES, max_length=1)
    email = models.EmailField(blank=True, null=True, unique=False)
    birth_date = models.DateField(null=True, blank=True)
    introduce = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    is_active = models.BooleanField(default=True)  # 기본 제공 필드지만 명시해도 OK
    deactivated_at = models.DateTimeField(null=True, blank=True)  # 탈퇴 시점 저장용 필드

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
        self.deactivated_at = timezone.now()  # 탈퇴 시점 저장
        self.save()

    def is_ready_for_deletion(self):
        if not self.is_active and hasattr(self, "deactivated_at"):
            return timezone.now() >= self.deactivated_at + timedelta(days=90)
        return False

    def __str__(self):
        return self.username


class ChatProfile(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_profiles"
    )
    chat_nickname = models.CharField(max_length=30)
    chat_description = models.CharField(max_length=100, blank=True, null=True)
    chat_profile_picture = models.ImageField(
        upload_to="chat_profiles/", blank=True, null=True
    )
    is_default = models.BooleanField(default=False)  # 기본 대화 프로필 설정

    def save(self, *args, **kwargs):
        if self.is_default:
            ChatProfile.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.chat_nickname}"


class Follow(models.Model):
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("from_user", "to_user")

    def __str__(self):  # 탈퇴 유저 처리 표시
        from_name = (
            self.from_user.nickname if self.from_user.is_active else "탈퇴한 사용자"
        )
        to_name = self.to_user.nickname if self.to_user.is_active else "탈퇴한 사용자"
        return f"{from_name} follows {to_name}"
