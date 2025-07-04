# Python Library
import uuid

# Third-Party Package
from django.db import models
from django.utils import timezone

# Local Apps
from accounts.models import User
from characters.models import Character


class Room(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rooms")
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name="rooms"
    )
    fixation = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "채팅방"
        verbose_name_plural = "채팅방들"

    def __str__(self):
        return f"{self.uuid} ({self.character})"


class Chat(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("ai", "AI"),
    ]

    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="chats")
    content = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    is_main = models.BooleanField(default=True)
    regeneration_group = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "채팅 메시지"
        verbose_name_plural = "채팅 메시지들"

    def __str__(self):
        return f"[{self.room.title}] {self.role}: {self.content[:30]}..."
