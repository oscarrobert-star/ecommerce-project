# notifications/models.py
from django.db import models


class Notification(models.Model):
    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push"),
    ]

    recipient = models.CharField(max_length=255)  # email, phone, device_id
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, default="pending")  # pending, sent, failed
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.channel} to {self.recipient} ({self.status})"

    class Meta:
        db_table = "notifications"


