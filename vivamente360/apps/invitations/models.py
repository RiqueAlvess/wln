import uuid
from django.db import models
from apps.core.models import TimeStampedModel
from apps.tenants.models import Empresa
from apps.structure.models import Unidade, Setor, Cargo
from apps.surveys.models import Campaign


class SurveyInvitation(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('sent', 'Enviado'),
        ('used', 'Utilizado'),
        ('expired', 'Expirado'),
    ]

    hash_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    email_encrypted = models.TextField()
    nome_encrypted = models.TextField(blank=True)

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'invitations_survey_invitation'
        verbose_name = 'Convite'
        verbose_name_plural = 'Convites'
        indexes = [
            models.Index(fields=['hash_token']),
            models.Index(fields=['campaign', 'status']),
        ]

    def __str__(self):
        return f"{self.campaign.nome} - {str(self.hash_token)[:8]}"
