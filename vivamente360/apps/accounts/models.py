from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.tenants.models import Empresa
from apps.structure.models import Unidade, Setor


class UserProfile(TimeStampedModel):
    ROLE_CHOICES = [
        ('rh', 'RH'),
        ('lideranca', 'Liderança'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)

    empresas = models.ManyToManyField(Empresa, blank=True, related_name='usuarios_rh')
    unidades_permitidas = models.ManyToManyField(Unidade, blank=True)
    setores_permitidos = models.ManyToManyField(Setor, blank=True)

    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'accounts_user_profile'
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class AuditLog(models.Model):
    ACOES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('import_csv', 'Importação CSV'),
        ('disparo_email', 'Disparo de E-mails'),
        ('export_relatorio', 'Exportação de Relatório'),
        ('create_campaign', 'Criação de Campanha'),
        ('view_dashboard', 'Visualização Dashboard'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=50, choices=ACOES)
    descricao = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_audit_log'
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['empresa', 'acao']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_acao_display()}"
