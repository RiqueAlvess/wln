"""
Django Admin para TaskQueue e UserNotification
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import TaskQueue, UserNotification


@admin.register(TaskQueue)
class TaskQueueAdmin(admin.ModelAdmin):
    """Admin para TaskQueue."""

    list_display = [
        'id', 'task_type_badge', 'status_badge', 'user', 'empresa',
        'progress_bar', 'file_available', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'task_type', 'created_at', 'empresa']
    search_fields = ['task_type', 'user__username', 'empresa__nome', 'error_message']
    readonly_fields = [
        'created_at', 'started_at', 'completed_at', 'attempts',
        'progress', 'progress_message', 'file_path', 'file_name', 'file_size'
    ]

    fieldsets = (
        ('Informações da Task', {
            'fields': ('task_type', 'status', 'user', 'empresa')
        }),
        ('Progresso', {
            'fields': ('progress', 'progress_message', 'attempts', 'max_attempts')
        }),
        ('Arquivo Gerado', {
            'fields': ('file_path', 'file_name', 'file_size'),
            'classes': ('collapse',)
        }),
        ('Payload e Erro', {
            'fields': ('payload', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
    )

    def task_type_badge(self, obj):
        """Exibe tipo de task com badge."""
        colors = {
            'export_plano_acao': 'info',
            'export_checklist_nr1': 'primary',
            'send_email': 'secondary',
            'generate_sector_analysis': 'warning',
        }
        color = colors.get(obj.task_type, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.task_type
        )
    task_type_badge.short_description = 'Tipo'

    def status_badge(self, obj):
        """Exibe status com badge colorido."""
        colors = {
            'pending': 'warning',
            'processing': 'info',
            'completed': 'success',
            'failed': 'danger'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def progress_bar(self, obj):
        """Exibe barra de progresso."""
        if obj.status == 'processing':
            return format_html(
                '<div style="width:100px;"><div class="progress"><div class="progress-bar" '
                'style="width:{}%">{} %</div></div></div>',
                obj.progress, obj.progress
            )
        return '-'
    progress_bar.short_description = 'Progresso'

    def file_available(self, obj):
        """Indica se arquivo está disponível."""
        if obj.can_download:
            return format_html('<span style="color: green;">✓ Disponível</span>')
        return '-'
    file_available.short_description = 'Arquivo'

    def has_add_permission(self, request):
        """Desabilita adição manual de tasks pelo admin."""
        return False


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    """Admin para UserNotification."""

    list_display = [
        'id', 'user', 'notification_type_badge', 'title',
        'is_read_icon', 'task_link', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at', 'empresa']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']

    fieldsets = (
        ('Usuário', {
            'fields': ('user', 'empresa')
        }),
        ('Notificação', {
            'fields': ('notification_type', 'title', 'message')
        }),
        ('Link e Task', {
            'fields': ('task', 'link_url', 'link_text')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'created_at')
        }),
    )

    def notification_type_badge(self, obj):
        """Exibe tipo de notificação com badge."""
        colors = {
            'task_completed': 'success',
            'task_failed': 'danger',
            'file_ready': 'primary',
            'info': 'info',
            'warning': 'warning',
            'error': 'danger'
        }
        color = colors.get(obj.notification_type, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Tipo'

    def is_read_icon(self, obj):
        """Ícone de lido/não lido."""
        if obj.is_read:
            return format_html('<span style="color: gray;">✓ Lida</span>')
        return format_html('<span style="color: blue;">● Nova</span>')
    is_read_icon.short_description = 'Status'

    def task_link(self, obj):
        """Link para a task relacionada."""
        if obj.task:
            return format_html(
                '<a href="/admin/core/taskqueue/{}/change/">Task #{}</a>',
                obj.task.id, obj.task.id
            )
        return '-'
    task_link.short_description = 'Task'

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Ação para marcar notificações como lidas."""
        from django.utils import timezone
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f'{updated} notificações marcadas como lidas.')
    mark_as_read.short_description = 'Marcar como lida'

    def mark_as_unread(self, request, queryset):
        """Ação para marcar notificações como não lidas."""
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(request, f'{updated} notificações marcadas como não lidas.')
    mark_as_unread.short_description = 'Marcar como não lida'
