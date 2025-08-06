from django.db import models


class UnreadNotificationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_read=False)