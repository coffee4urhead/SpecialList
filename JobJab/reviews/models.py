from JobJab.settings import AUTH_USER_MODEL
from django.db import models

class Review(models.Model):
    reviewer = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='given_reviews')
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    rating = models.SmallIntegerField()
    main_caption = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    #Adding a constraint or logic to prevent multiple reviews by the same reviewer on the same service/booking would improve data quality.

    def __str__(self):
        return f"{self.main_caption} - {self.rating}"