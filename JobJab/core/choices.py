from django.db import models


class UserChoices(models.TextChoices):
    SEEKER = 'seeker', 'Seeker'
    PROVIDER = 'provider', 'Provider'