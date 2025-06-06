from django.db import models
from django.utils import timezone


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ("user", "User"),
        ("ai", "AI"),
    ]

    content = models.TextField(verbose_name="대화 내용")
    sender = models.CharField(
        max_length=10, choices=SENDER_CHOICES, verbose_name="발신자"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성시간")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정시간")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "채팅 메시지"
        verbose_name_plural = "채팅 메시지들"

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..."
