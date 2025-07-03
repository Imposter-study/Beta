from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random
from allauth.socialaccount.models import SocialAccount


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

    username = models.CharField(max_length=20, unique=True)
    nickname = models.CharField(max_length=30, unique=True, blank=True, null=True)
    gender = models.CharField(default="O", choices=GENDER_CHOICES, max_length=1)
    email = models.EmailField(blank=True, null=True, unique=False)
    birth_date = models.DateField(null=True, blank=True)
    introduce = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )

    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

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
        self.username = f"deleted_user_{self.id}"
        self.nickname = "탈퇴한 사용자"  # 탈퇴 사용자는 나중에 "탈퇴한 사용자"로 표시되도록 프론트에서 조건 분기하면 됩니다.
        self.email = f"deleted_{self.id}@deleted.com"
        self.introduce = None
        self.profile_picture = None
        self.birth_date = None
        self.gender = "O"
        self.deactivated_at = timezone.now()
        SocialAccount.objects.filter(
            user=self
        ).delete()  # 소셜 계정이 연결되어 있다면 삭제
        self.save()

    def is_ready_for_deletion(self):
        if self.is_deactivated and self.deactivated_at:
            return timezone.now() >= self.deactivated_at + timedelta(days=90)
        return False

    def __str__(self):
        return self.username


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

    def __str__(self):
        return f"{self.from_user} follows {self.to_user}"
