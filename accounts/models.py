from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    GENDER_CHOICES = [("M", "남자"), ("F", "여자"), ("O", "기타")]
    
    username = models.CharField(max_length=20, unique=True)
    nickname = models.CharField(max_length=20, unique=True)
    gender = models.CharField(
        choices=GENDER_CHOICES, max_length=1, blank=True, null=True
        )
    age = models.IntegerField(blank=True, null=True)
    introduce = models.TextField(blank=True, null=True)
    # profilepicture = models.ImageField(blank=True, null=True)
    # follower = models.ManyToManyField(
    #    "self", symmetrical=False, related_name="following", blank=True
    # )
