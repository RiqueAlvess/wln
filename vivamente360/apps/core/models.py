from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TaskQueue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    task_type = models.CharField(max_length=50)
    payload = models.JSONField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
        db_table = 'core_task_queue'

    def __str__(self):
        return f"{self.task_type} - {self.status}"
