from django.db import models
from apps.core.models import TimeStampedModel
from apps.surveys.models import Campaign, Pergunta
from apps.structure.models import Setor
from apps.tenants.models import Empresa


class DimTempo(models.Model):
    data = models.DateField(unique=True)
    ano = models.IntegerField()
    mes = models.IntegerField()
    trimestre = models.IntegerField()
    semana_ano = models.IntegerField()
    dia_semana = models.IntegerField()
    nome_mes = models.CharField(max_length=20)

    class Meta:
        db_table = 'analytics_dim_tempo'
        verbose_name = 'Dimensão Tempo'
        verbose_name_plural = 'Dimensões Tempo'

    def __str__(self):
        return str(self.data)


class DimEstrutura(models.Model):
    empresa_id = models.IntegerField()
    empresa_nome = models.CharField(max_length=255)
    unidade_id = models.IntegerField()
    unidade_nome = models.CharField(max_length=255)
    setor_id = models.IntegerField()
    setor_nome = models.CharField(max_length=255)
    cargo_id = models.IntegerField()
    cargo_nome = models.CharField(max_length=255)
    cargo_nivel = models.CharField(max_length=50)

    class Meta:
        db_table = 'analytics_dim_estrutura'
        verbose_name = 'Dimensão Estrutura'
        verbose_name_plural = 'Dimensões Estrutura'
        unique_together = ['empresa_id', 'unidade_id', 'setor_id', 'cargo_id']

    def __str__(self):
        return f"{self.empresa_nome} - {self.unidade_nome} - {self.setor_nome}"


class DimDemografia(models.Model):
    faixa_etaria = models.CharField(max_length=10)
    tempo_empresa = models.CharField(max_length=10)
    genero = models.CharField(max_length=1)

    class Meta:
        db_table = 'analytics_dim_demografia'
        verbose_name = 'Dimensão Demografia'
        verbose_name_plural = 'Dimensões Demografia'
        unique_together = ['faixa_etaria', 'tempo_empresa', 'genero']

    def __str__(self):
        return f"{self.faixa_etaria} - {self.tempo_empresa} - {self.genero}"


class DimDimensaoHSE(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10)

    class Meta:
        db_table = 'analytics_dim_dimensao_hse'
        verbose_name = 'Dimensão HSE'
        verbose_name_plural = 'Dimensões HSE'

    def __str__(self):
        return self.nome


class FactScoreDimensao(TimeStampedModel):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    dim_tempo = models.ForeignKey(DimTempo, on_delete=models.CASCADE)
    dim_estrutura = models.ForeignKey(DimEstrutura, on_delete=models.CASCADE)
    dim_demografia = models.ForeignKey(DimDemografia, on_delete=models.CASCADE)
    dim_hse = models.ForeignKey(DimDimensaoHSE, on_delete=models.CASCADE)

    score_medio = models.DecimalField(max_digits=4, decimal_places=2)
    probabilidade = models.IntegerField()
    severidade = models.IntegerField()
    nivel_risco = models.IntegerField()
    classificacao = models.CharField(max_length=20)
    cor = models.CharField(max_length=10)

    total_respostas = models.IntegerField()

    class Meta:
        db_table = 'analytics_fact_score_dimensao'
        verbose_name = 'Fato Score Dimensão'
        verbose_name_plural = 'Fatos Score Dimensão'
        indexes = [
            models.Index(fields=['campaign', 'dim_estrutura']),
            models.Index(fields=['campaign', 'dim_hse']),
            models.Index(fields=['campaign', 'classificacao']),
        ]

    def __str__(self):
        return f"{self.campaign.nome} - {self.dim_hse.nome}"


class FactIndicadorCampanha(TimeStampedModel):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    dim_tempo = models.ForeignKey(DimTempo, on_delete=models.CASCADE)
    dim_estrutura = models.ForeignKey(DimEstrutura, on_delete=models.CASCADE)

    total_convidados = models.IntegerField()
    total_respondidos = models.IntegerField()
    percentual_adesao = models.DecimalField(max_digits=5, decimal_places=2)

    total_risco_critico = models.IntegerField()
    total_risco_importante = models.IntegerField()
    total_risco_moderado = models.IntegerField()
    total_risco_aceitavel = models.IntegerField()

    percentual_risco_alto = models.DecimalField(max_digits=5, decimal_places=2)
    igrp_score = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        db_table = 'analytics_fact_indicador_campanha'
        verbose_name = 'Fato Indicador Campanha'
        verbose_name_plural = 'Fatos Indicadores Campanha'

    def __str__(self):
        return f"{self.campaign.nome} - Indicadores"


class FactRespostaPergunta(TimeStampedModel):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    dim_estrutura = models.ForeignKey(DimEstrutura, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)

    qtd_valor_0 = models.IntegerField(default=0)
    qtd_valor_1 = models.IntegerField(default=0)
    qtd_valor_2 = models.IntegerField(default=0)
    qtd_valor_3 = models.IntegerField(default=0)
    qtd_valor_4 = models.IntegerField(default=0)

    media = models.DecimalField(max_digits=4, decimal_places=2)
    total_respostas = models.IntegerField()

    class Meta:
        db_table = 'analytics_fact_resposta_pergunta'
        verbose_name = 'Fato Resposta Pergunta'
        verbose_name_plural = 'Fatos Respostas Perguntas'

    def __str__(self):
        return f"{self.campaign.nome} - P{self.pergunta.numero}"


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
