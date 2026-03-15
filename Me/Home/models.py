from django.db import models


class Subscriber(models.Model):
    email = models.CharField(max_length=254)
        # email addresses cannot be longer than 254 characters 


class Visit(models.Model):
    path = models.CharField(max_length=255, db_index=True)
    visitor_fingerprint = models.CharField(max_length=64, db_index=True)
    ip_hash = models.CharField(max_length=64, db_index=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)
    referrer = models.CharField(max_length=1024, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    visit_day = models.DateField(db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.path} @ {self.created_at.isoformat()}"
