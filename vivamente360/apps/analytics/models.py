from django.db import models
from apps.core.models import TimeStampedModel
from apps.surveys.models import Campaign
from apps.structure.models import Setor
from apps.tenants.models import Empresa


class SectorAnalysis(TimeStampedModel):
    """
    Model para armazenar análises de setor geradas por IA
    """
    STATUS_CHOICES = [
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sector_analyses')
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name='analyses')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='sector_analyses')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')

    # Dados da análise (JSON)
    diagnostico = models.TextField(blank=True)
    fatores_contribuintes = models.JSONField(default=list)
    pontos_atencao = models.JSONField(default=list)
    pontos_fortes = models.JSONField(default=list)
    recomendacoes = models.JSONField(default=list)
    impacto_esperado = models.TextField(blank=True)
    alertas_sentimento = models.JSONField(default=list)

    # Metadados
    total_respostas = models.IntegerField(default=0)
    scores = models.JSONField(default=dict)  # Scores por dimensão
    generated_by = models.CharField(max_length=100, default='GPT-4o')
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'analytics_sector_analysis'
        verbose_name = 'Análise de Setor'
        verbose_name_plural = 'Análises de Setores'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa', 'campaign']),
            models.Index(fields=['setor', 'campaign']),
            models.Index(fields=['status']),
        ]
        unique_together = ['setor', 'campaign']

    def __str__(self):
        return f"Análise {self.setor.nome} - {self.campaign.nome}"
