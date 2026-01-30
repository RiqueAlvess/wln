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

    def encerrar(self):
        """
        Encerra a campanha e invalida todos os convites pendentes ou enviados.

        Returns:
            dict: Dicionário com informações sobre a operação:
                - success (bool): Se a operação foi bem-sucedida
                - invalidated_count (int): Quantidade de convites invalidados
                - message (str): Mensagem descritiva
        """
        from apps.invitations.models import SurveyInvitation
        from django.utils import timezone

        # Verifica se a campanha já está encerrada
        if self.status == 'closed':
            return {
                'success': False,
                'invalidated_count': 0,
                'message': 'Campanha já está encerrada.'
            }

        # Contar convites que serão invalidados
        convites_para_invalidar = SurveyInvitation.objects.filter(
            campaign=self,
            status__in=['pending', 'sent']
        )
        count = convites_para_invalidar.count()

        # Atualizar status da campanha
        self.status = 'closed'
        self.save()

        # Invalidar todos os convites pendentes ou enviados
        convites_para_invalidar.update(
            status='expired',
            updated_at=timezone.now()
        )

        return {
            'success': True,
            'invalidated_count': count,
            'message': f'Campanha encerrada com sucesso. {count} convite(s) invalidado(s).'
        }

    def contar_convites_ativos(self):
        """
        Retorna a contagem de convites ativos (pendentes + enviados).

        Returns:
            dict: Dicionário com contagens:
                - pendentes (int): Convites com status 'pending'
                - enviados (int): Convites com status 'sent'
                - total_ativos (int): Total de convites ativos
        """
        from apps.invitations.models import SurveyInvitation

        pendentes = SurveyInvitation.objects.filter(
            campaign=self,
            status='pending'
        ).count()

        enviados = SurveyInvitation.objects.filter(
            campaign=self,
            status='sent'
        ).count()

        return {
            'pendentes': pendentes,
            'enviados': enviados,
            'total_ativos': pendentes + enviados
        }


class CategoriaFatorRisco(TimeStampedModel):
    """Categorias principais de fatores de risco conforme NR-1"""

    CATEGORIAS = [
        ('organizacao', 'Organização do Trabalho'),
        ('conteudo', 'Conteúdo do Trabalho'),
        ('relacoes', 'Relações Interpessoais'),
        ('individuais', 'Fatores Individuais/Contextuais'),
    ]

    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    icone = models.CharField(max_length=50, default='bi-exclamation-triangle')
    ordem = models.IntegerField(default=0)

    class Meta:
        db_table = 'surveys_categoria_fator_risco'
        ordering = ['ordem']
        verbose_name = 'Categoria de Fator de Risco'
        verbose_name_plural = 'Categorias de Fatores de Risco'

    def __str__(self):
        return self.nome


class FatorRisco(TimeStampedModel):
    """Fatores de risco psicossociais específicos dentro de cada categoria (NR-1)"""

    categoria = models.ForeignKey(
        CategoriaFatorRisco,
        on_delete=models.CASCADE,
        related_name='fatores'
    )
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    exemplos = models.TextField(
        help_text="Exemplos práticos deste fator de risco"
    )

    # Mapeamento para Dimensões HSE-IT
    dimensoes_hse = models.ManyToManyField(
        'Dimensao',
        related_name='fatores_risco',
        help_text="Dimensões HSE-IT relacionadas a este fator"
    )

    # Severidade base (pode ser ajustada por CNAE)
    severidade_base = models.IntegerField(
        default=3,
        help_text="1=Leve, 2=Moderado, 3=Significativo, 4=Grave, 5=Catastrófico"
    )

    # Consequências possíveis
    CONSEQUENCIAS_CHOICES = [
        ('saude_mental', 'Danos à Saúde Mental'),
        ('saude_fisica', 'Danos Físicos'),
        ('acidentes', 'Acidentes de Trabalho'),
    ]

    consequencias = models.JSONField(
        default=list,
        help_text="Lista de consequências possíveis (saude_mental, saude_fisica, acidentes)"
    )

    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'surveys_fator_risco'
        ordering = ['categoria', 'nome']
        verbose_name = 'Fator de Risco Psicossocial'
        verbose_name_plural = 'Fatores de Risco Psicossociais'

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class SeveridadePorCNAE(TimeStampedModel):
    """Ajuste de severidade de fator de risco baseado no CNAE da empresa"""

    fator_risco = models.ForeignKey(
        FatorRisco,
        on_delete=models.CASCADE,
        related_name='severidades_cnae'
    )
    cnae_secao = models.CharField(
        max_length=1,
        help_text="Seção CNAE (A-U)"
    )
    cnae_divisao = models.CharField(
        max_length=2,
        blank=True,
        help_text="Divisão CNAE (01-99) - Opcional para especificar melhor"
    )

    severidade_ajustada = models.IntegerField(
        help_text="Severidade específica para este CNAE (1-5)"
    )
    justificativa = models.TextField(
        help_text="Por que este CNAE tem severidade diferente da base"
    )

    class Meta:
        db_table = 'surveys_severidade_cnae'
        unique_together = ['fator_risco', 'cnae_secao', 'cnae_divisao']
        verbose_name = 'Severidade por CNAE'
        verbose_name_plural = 'Severidades por CNAE'

    def __str__(self):
        cnae = f"{self.cnae_secao}{self.cnae_divisao}" if self.cnae_divisao else self.cnae_secao
        return f"{self.fator_risco.codigo} - CNAE {cnae}: S={self.severidade_ajustada}"
