from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    Custom User model to include apartment_id.
    Email is used for authentication as per allauth settings.
    """
    apartment_id = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., apt123")

    def __str__(self):
        return self.email if self.email else self.username

class Apartment(models.Model):
    """
    Represents an apartment group.
    """
    apartment_id = models.CharField(max_length=100, unique=True) # e.g., "apt123"

    def __str__(self):
        return self.apartment_id

class ScheduleSlot(models.Model):
    """
    Represents a booked slot for bathroom or kitchen.
    """
    SLOT_TYPES = [
        ('bathroom', 'Bathroom (15 min)'),
        ('kitchen', 'Kitchen (1 hour)'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    slot_type = models.CharField(max_length=10, choices=SLOT_TYPES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        ordering = ['start_time']
        unique_together = ('apartment', 'start_time', 'end_time', 'slot_type') # Prevent exact duplicates

    def __str__(self):
        return f"{self.apartment.apartment_id} - {self.user.email} - {self.slot_type} {self.start_time.strftime('%Y-%m-%d %H:%M')}-{self.end_time.strftime('%H:%M')}"

class ChatMessage(models.Model):
    """
    Represents a chat message within an apartment group.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.apartment.apartment_id} - {self.user.email} - {self.timestamp.strftime('%H:%M')}: {self.message[:50]}..."