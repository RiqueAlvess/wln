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
