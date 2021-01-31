from django.db import models

# Create your models here.
class Subscriber(models.Model):
    email = models.CharField(max_length=254)
        # email addresses cannot be longer than 254 characters 