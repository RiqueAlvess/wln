from django.db import models
from apps.core.models import TimeStampedModel
from apps.tenants.models import Empresa


class Unidade(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='unidades')
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=50, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'structure_unidade'
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'
        ordering = ['nome']
        unique_together = ['empresa', 'nome']

    def __str__(self):
        return f"{self.empresa.nome} - {self.nome}"


class Setor(TimeStampedModel):
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='setores')
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=50, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'structure_setor'
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        ordering = ['nome']
        unique_together = ['unidade', 'nome']

    def __str__(self):
        return f"{self.unidade.nome} - {self.nome}"


class Cargo(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='cargos')
    nome = models.CharField(max_length=255)
    nivel = models.CharField(max_length=50, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'structure_cargo'
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['nome']
        unique_together = ['empresa', 'nome']

    def __str__(self):
        return self.nome
