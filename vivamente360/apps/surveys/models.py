from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.tenants.models import Empresa


class Dimensao(TimeStampedModel):
    TIPO_CHOICES = [
        ('negativo', 'Negativo'),
        ('positivo', 'Positivo'),
    ]

    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    descricao = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'surveys_dimensao'
        verbose_name = 'Dimensão'
        verbose_name_plural = 'Dimensões'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class Pergunta(TimeStampedModel):
    dimensao = models.ForeignKey(Dimensao, on_delete=models.CASCADE, related_name='perguntas')
    numero = models.IntegerField()
    texto = models.TextField()
    texto_ajuda = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'surveys_pergunta'
        verbose_name = 'Pergunta'
        verbose_name_plural = 'Perguntas'
        ordering = ['numero']
        unique_together = ['dimensao', 'numero']

    def __str__(self):
        return f"Q{self.numero}: {self.texto[:50]}"


class Campaign(TimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('active', 'Ativa'),
        ('closed', 'Encerrada'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='campaigns')
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'surveys_campaign'
        verbose_name = 'Campanha'
        verbose_name_plural = 'Campanhas'
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.empresa.nome} - {self.nome}"
