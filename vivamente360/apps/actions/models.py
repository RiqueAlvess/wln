from django.db import models
from apps.core.models import TimeStampedModel
from apps.tenants.models import Empresa
from apps.surveys.models import Campaign, Dimensao


class PlanoAcao(TimeStampedModel):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    dimensao = models.ForeignKey(Dimensao, on_delete=models.CASCADE)

    nivel_risco = models.CharField(max_length=20)
    descricao_risco = models.TextField()
    acao_proposta = models.TextField()
    responsavel = models.CharField(max_length=255)
    prazo = models.DateField()
    recursos_necessarios = models.TextField(blank=True)
    indicadores = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')

    class Meta:
        db_table = 'actions_plano_acao'
        verbose_name = 'Plano de Ação'
        verbose_name_plural = 'Planos de Ação'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.dimensao.nome} - {self.nivel_risco}"
