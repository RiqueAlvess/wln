import uuid
import hashlib
import secrets
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.tenants.models import Empresa


class AnonymousReport(TimeStampedModel):
    """
    Canal de denúncia anônima.

    Anonimidade garantida:
    - Sem FK para User, SurveyInvitation ou qualquer identificador pessoal
    - Protocolo gerado com hash aleatório (não derivado de dados pessoais)
    - IP do remetente NÃO é armazenado
    - Sem timestamps de precisão (arredondado para hora cheia para evitar correlação temporal)
    """

    CATEGORIA_CHOICES = [
        ('assedio_moral', 'Assédio Moral'),
        ('assedio_sexual', 'Assédio Sexual'),
        ('discriminacao', 'Discriminação'),
        ('seguranca', 'Segurança do Trabalho'),
        ('etica', 'Violação de Ética'),
        ('corrupcao', 'Corrupção/Fraude'),
        ('ambiente', 'Ambiente de Trabalho Hostil'),
        ('outros', 'Outros'),
    ]

    GRAVIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('em_analise', 'Em Análise'),
        ('investigando', 'Investigando'),
        ('resolvida', 'Resolvida'),
        ('arquivada', 'Arquivada'),
    ]

    # Protocolo anônimo - gerado aleatoriamente, sem derivação de dados pessoais
    protocolo = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        editable=False,
        help_text="Código de protocolo anônimo para acompanhamento"
    )

    # Chave de acesso para o denunciante acompanhar (hash de token secreto)
    access_token_hash = models.CharField(
        max_length=64,
        editable=False,
        help_text="Hash SHA-256 do token de acesso do denunciante"
    )

    # Dados da denúncia - sem qualquer informação identificável
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='denuncias'
    )
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    gravidade = models.CharField(max_length=10, choices=GRAVIDADE_CHOICES, default='media')
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(
        help_text="Descrição detalhada da denúncia"
    )

    # Contexto genérico (sem identificar setor/cargo específico para preservar anonimato)
    local_ocorrencia = models.CharField(
        max_length=255,
        blank=True,
        help_text="Local genérico da ocorrência (ex: 'escritório', 'fábrica')"
    )
    data_ocorrencia_aproximada = models.CharField(
        max_length=50,
        blank=True,
        help_text="Data aproximada (ex: 'início de março 2026', 'últimas semanas')"
    )

    # Status e gestão pelo RH
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='aberta')
    prioridade_rh = models.IntegerField(
        default=0,
        help_text="Prioridade definida pelo RH (0=não definida, 1-5)"
    )

    # Timestamp arredondado para hora cheia (anti-correlação temporal)
    reported_at = models.DateTimeField(
        help_text="Hora arredondada do reporte (para evitar correlação temporal)"
    )

    class Meta:
        db_table = 'reports_anonymous_report'
        verbose_name = 'Denúncia Anônima'
        verbose_name_plural = 'Denúncias Anônimas'
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['empresa', 'categoria']),
            models.Index(fields=['protocolo']),
        ]

    def __str__(self):
        return f"[{self.protocolo}] {self.get_categoria_display()} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.protocolo:
            self.protocolo = self._generate_protocolo()
        if not self.reported_at:
            # Arredondar para hora cheia para evitar correlação temporal
            now = timezone.now()
            self.reported_at = now.replace(minute=0, second=0, microsecond=0)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_protocolo():
        """Gera protocolo aleatório de 12 caracteres alfanuméricos."""
        return secrets.token_hex(6).upper()

    @staticmethod
    def hash_access_token(token):
        """Gera hash SHA-256 do token de acesso."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def generate_access_token():
        """Gera token de acesso seguro para o denunciante."""
        return secrets.token_urlsafe(32)


class ReportResponse(TimeStampedModel):
    """
    Respostas/atualizações do RH para denúncias.

    O denunciante pode ver estas respostas usando seu protocolo + token.
    """
    report = models.ForeignKey(
        AnonymousReport,
        on_delete=models.CASCADE,
        related_name='respostas_rh'
    )
    mensagem = models.TextField(
        help_text="Resposta ou atualização do RH"
    )
    # Quem respondeu do RH (visível apenas internamente)
    respondido_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        help_text="Usuário RH que respondeu (não visível ao denunciante)"
    )
    # Mudança de status associada
    novo_status = models.CharField(
        max_length=15,
        choices=AnonymousReport.STATUS_CHOICES,
        blank=True,
        help_text="Novo status após esta resposta"
    )
    visivel_denunciante = models.BooleanField(
        default=True,
        help_text="Se esta resposta é visível para o denunciante"
    )

    class Meta:
        db_table = 'reports_report_response'
        verbose_name = 'Resposta de Denúncia'
        verbose_name_plural = 'Respostas de Denúncias'
        ordering = ['created_at']

    def __str__(self):
        return f"Resposta para [{self.report.protocolo}]"


class ReportFollowUp(TimeStampedModel):
    """
    Mensagens adicionais do denunciante anônimo.
    Permite que o denunciante adicione informações sem se identificar.
    """
    report = models.ForeignKey(
        AnonymousReport,
        on_delete=models.CASCADE,
        related_name='followups'
    )
    mensagem = models.TextField(
        help_text="Informação adicional do denunciante"
    )

    class Meta:
        db_table = 'reports_report_followup'
        verbose_name = 'Complemento de Denúncia'
        verbose_name_plural = 'Complementos de Denúncias'
        ordering = ['created_at']

    def __str__(self):
        return f"Complemento para [{self.report.protocolo}]"
