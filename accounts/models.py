from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    GENDER_CHOICES = [("M", "남자"), ("F", "여자"), ("O", "기타")]

    username = models.CharField(max_length=20, unique=True)
    nickname = models.CharField(max_length=20, unique=True)
    gender = models.CharField(default="O", choices=GENDER_CHOICES, max_length=1)
    email = models.EmailField(blank=True, null=True, unique=False)
    birth_date = models.DateField(null=True, blank=True)
    introduce = models.TextField(blank=True, null=True)

    # profilepicture = models.ImageField(blank=True, null=True)
    # follower = models.ManyToManyField(
    #    "self", symmetrical=False, related_name="following", blank=True
    # )
    def mark_as_deactivated(self):
        self.is_active = False
        self.save()

    def is_ready_for_deletion(self):
        if self.is_deactivated and self.deactivated_at:
            return timezone.now() >= self.deactivated_at + timedelta(days=90)
        return False

    def __str__(self):
        return self.username
