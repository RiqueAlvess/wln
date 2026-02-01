"""
Serializers para TaskQueue e UserNotification
"""
from rest_framework import serializers
from .models import TaskQueue, UserNotification


class TaskQueueSerializer(serializers.ModelSerializer):
    """Serializer para TaskQueue."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_file_task = serializers.BooleanField(read_only=True)
    can_download = serializers.BooleanField(read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = TaskQueue
        fields = [
            'id', 'task_type', 'status', 'status_display',
            'progress', 'progress_message',
            'file_name', 'file_size', 'file_path',
            'is_file_task', 'can_download',
            'error_message', 'attempts', 'max_attempts',
            'created_at', 'started_at', 'completed_at',
            'duration'
        ]

    def get_duration(self, obj):
        """Retorna duração da task em segundos."""
        if obj.started_at and obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return delta.total_seconds()
        return None


class UserNotificationSerializer(serializers.ModelSerializer):
    """Serializer para UserNotification."""

    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    task_info = TaskQueueSerializer(source='task', read_only=True)
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = UserNotification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'message', 'link_url', 'link_text',
            'is_read', 'read_at', 'created_at',
            'task', 'task_info', 'time_ago'
        ]
        read_only_fields = ['created_at', 'read_at']

    def get_time_ago(self, obj):
        """Retorna tempo desde criação em formato amigável."""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        delta = now - obj.created_at

        if delta < timedelta(minutes=1):
            return 'agora mesmo'
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f'há {minutes} minuto{"s" if minutes > 1 else ""}'
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f'há {hours} hora{"s" if hours > 1 else ""}'
        elif delta < timedelta(days=7):
            days = delta.days
            return f'há {days} dia{"s" if days > 1 else ""}'
        else:
            return obj.created_at.strftime('%d/%m/%Y %H:%M')


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer para marcar notificações como lidas."""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )
