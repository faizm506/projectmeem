from django.db import models


class PaymentEvent(models.Model):
    """Log of webhook events we already handled. Stops the same event being processed twice."""

    provider = models.CharField(max_length=20)
    event_id = models.CharField(max_length=100, unique=True)
    event_type = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider}:{self.event_id}"
