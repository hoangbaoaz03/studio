from django.db import models
from django.conf import settings
from course.models import Course

class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_sessions')
    conversation_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"Chat Session: {self.user.username} - {self.course.title if self.course else 'General'}"

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('model', 'Model'), # Gemini uses 'model' instead of 'assistant' usually, but let's stick to standard internal 'assistant' or 'model'. Gemini dicts use 'user' and 'model'. Let's use 'model' for Gemini compatibility.
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    context_used = models.TextField(blank=True, null=True, help_text="RAG Context used")
    tokens_used = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role} at {self.created_at}"
