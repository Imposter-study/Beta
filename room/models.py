from django.db import models
from django.utils import timezone


class Room(models.Model):
    """채팅방 모델, 각 챗봇마다 하나씩"""

    room_id = models.AutoField(primary_key=True)
    character_id = models.CharField(
        max_length=50, unique=True, verbose_name="챗봇 ID"
    )
    title = models.CharField(max_length=200, verbose_name="채팅방 제목")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성시간")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정시간")

    class Meta:
        verbose_name = "채팅방"
        verbose_name_plural = "채팅방들"

    def __str__(self):
        return f"{self.title} ({self.character_id})"


class Chat(models.Model):
    """채팅 메시지 모델"""

    ROLE_CHOICES = [
        ("user", "User"),
        ("ai", "AI"),
    ]

    chat_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="chats", verbose_name="채팅방"
    )
    content = models.TextField(verbose_name="메시지 내용")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="역할")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성시간")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정시간")

    class Meta:
        ordering = ["created_at"]
        verbose_name = "채팅 메시지"
        verbose_name_plural = "채팅 메시지들"

    def __str__(self):
        return f"[{self.room.title}] {self.role}: {self.content[:30]}..."
