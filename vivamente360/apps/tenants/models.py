from django.db import models
from apps.core.models import TimeStampedModel


class Empresa(TimeStampedModel):
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, unique=True)
    total_funcionarios = models.IntegerField(default=0)

    # CNAE para análise de riscos específicos por setor econômico
    cnae = models.CharField(
        max_length=10,
        blank=True,
        help_text="Código CNAE principal da empresa (ex: 62.01-5)"
    )
    cnae_descricao = models.CharField(
        max_length=255,
        blank=True,
        help_text="Descrição da atividade CNAE"
    )

    logo_url = models.URLField(blank=True)
    favicon_url = models.URLField(blank=True)
    cor_primaria = models.CharField(max_length=7, default='#0d6efd')
    cor_secundaria = models.CharField(max_length=7, default='#6c757d')
    cor_fonte = models.CharField(max_length=7, default='#ffffff', help_text='Cor da fonte nos botões e elementos primários')
    nome_app = models.CharField(max_length=100, default='VIVAMENTE 360º')

    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'tenants_empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome']

    def __str__(self):
        return self.nome
