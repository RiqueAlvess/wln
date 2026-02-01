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

    # Campos para rastreamento de arquivos gerados
    file_path = models.CharField(max_length=500, blank=True, help_text='Caminho do arquivo gerado')
    file_name = models.CharField(max_length=255, blank=True, help_text='Nome do arquivo para download')
    file_size = models.IntegerField(null=True, blank=True, help_text='Tamanho do arquivo em bytes')

    # Campos para rastreamento de progresso
    progress = models.IntegerField(default=0, help_text='Progresso da task (0-100)')
    progress_message = models.CharField(max_length=255, blank=True, help_text='Mensagem de progresso')

    # Campos para usuário e empresa
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    empresa = models.ForeignKey('tenants.Empresa', on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['empresa', 'status']),
        ]
        db_table = 'core_task_queue'

    def __str__(self):
        return f"{self.task_type} - {self.status}"

    @property
    def is_file_task(self):
        """Retorna True se a task gera um arquivo."""
        return self.task_type in [
            'export_plano_acao',
            'export_plano_acao_rich',
            'export_checklist_nr1',
            'export_campaign_comparison',
            'export_risk_matrix_excel',
            'export_pgr_document',
        ]

    @property
    def can_download(self):
        """Retorna True se o arquivo está disponível para download."""
        return self.status == 'completed' and bool(self.file_path)


class UserNotificationManager(models.Manager):
    """Manager customizado para UserNotification."""

    def active(self):
        """Retorna apenas notificações não expiradas (últimas 24h)."""
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(hours=24)
        return self.filter(created_at__gte=cutoff)

    def delete_expired(self):
        """Deleta notificações mais antigas que 24 horas."""
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(hours=24)
        deleted, _ = self.filter(created_at__lt=cutoff).delete()
        return deleted


class UserNotification(models.Model):
    """
    Notificações para usuários sobre tasks completadas, erros, etc.

    Notificações são automaticamente deletadas após 24 horas.
    """
    TYPE_CHOICES = [
        ('task_completed', 'Task Completada'),
        ('task_failed', 'Task Falhou'),
        ('file_ready', 'Arquivo Pronto'),
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='notifications')
    empresa = models.ForeignKey('tenants.Empresa', on_delete=models.CASCADE, null=True, blank=True)

    objects = UserNotificationManager()

    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()

    # Link relacionado (task, arquivo, etc)
    task = models.ForeignKey(TaskQueue, on_delete=models.CASCADE, null=True, blank=True)
    link_url = models.CharField(max_length=500, blank=True)
    link_text = models.CharField(max_length=100, blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_user_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def mark_as_read(self):
        """Marca notificação como lida."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
