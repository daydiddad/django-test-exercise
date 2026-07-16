from datetime import timedelta
from django.db import models
from django.utils import timezone


# Create your models here.


class Task(models.Model):
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)
    posted_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)

    def is_overdue(self, dt):
        if self.due_at is None:
            return False
        return self.due_at < dt

    def is_due_soon(self, dt=None):
        if self.due_at is None:
            return False
        current = dt or timezone.now()
        window_end = current + timedelta(days=1)
        return self.due_at <= window_end and self.due_at >= current

    def urgency_label(self):
        if self.completed:
            return 'Completed'
        if self.due_at is None:
            return 'No Deadline'
        if self.is_overdue(timezone.now()):
            return 'Overdue'
        if self.is_due_soon():
            return 'Due Soon'
        return 'On Track'
