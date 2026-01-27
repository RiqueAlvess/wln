from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.tenants.models import Empresa
from apps.surveys.models import Campaign, Dimensao


class ChecklistEtapa(TimeStampedModel):
    ETAPAS = [
        (1, 'Preparação'),
        (2, 'Identificação de Perigos'),
        (3, 'Avaliação de Riscos'),
        (4, 'Planejamento e Controle'),
        (5, 'Monitoramento e Revisão'),
        (6, 'Comunicação e Cultura'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    etapa = models.IntegerField(choices=ETAPAS)
    item_texto = models.TextField()
    item_ordem = models.IntegerField()
    concluido = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    responsavel = models.CharField(max_length=255, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        db_table = 'actions_checklist_etapa'
        verbose_name = 'Checklist Etapa'
        verbose_name_plural = 'Checklists Etapas'
        unique_together = ['empresa', 'campaign', 'etapa', 'item_ordem']
        ordering = ['etapa', 'item_ordem']

    def __str__(self):
        return f"Etapa {self.etapa} - Item {self.item_ordem}"


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


class Evidencia(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    checklist_item = models.ForeignKey(ChecklistEtapa, on_delete=models.SET_NULL, null=True, blank=True)
    plano_acao = models.ForeignKey(PlanoAcao, on_delete=models.SET_NULL, null=True, blank=True)

    arquivo = models.FileField(upload_to='evidencias/%Y/%m/')
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=50)

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'actions_evidencia'
        verbose_name = 'Evidência'
        verbose_name_plural = 'Evidências'
        ordering = ['-created_at']

    def __str__(self):
        return f"Evidência {self.tipo} - {self.campaign.nome}"
