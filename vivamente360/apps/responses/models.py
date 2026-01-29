from django.db import models
from apps.core.models import TimeStampedModel
from apps.structure.models import Unidade, Setor, Cargo
from apps.surveys.models import Campaign


class SurveyResponse(TimeStampedModel):
    FAIXA_ETARIA_CHOICES = [
        ('18-24', '18 a 24 anos'),
        ('25-34', '25 a 34 anos'),
        ('35-49', '35 a 49 anos'),
        ('50-59', '50 a 59 anos'),
        ('60+', '60 anos ou mais'),
    ]

    TEMPO_EMPRESA_CHOICES = [
        ('0-1', 'Menos de 1 ano'),
        ('1-3', '1 a 3 anos'),
        ('3-5', '3 a 5 anos'),
        ('5-10', '5 a 10 anos'),
        ('10+', 'Mais de 10 anos'),
    ]

    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('N', 'Prefiro não informar'),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='responses')
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)

    faixa_etaria = models.CharField(max_length=10, choices=FAIXA_ETARIA_CHOICES)
    tempo_empresa = models.CharField(max_length=10, choices=TEMPO_EMPRESA_CHOICES)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES)

    respostas = models.JSONField()

    # Campo de feedback livre
    comentario_livre = models.TextField(
        blank=True,
        help_text="Comentário opcional do colaborador"
    )

    # Análise de sentimento (preenchido pela IA)
    sentimento_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="-1.0 (muito negativo) a 1.0 (muito positivo)"
    )
    sentimento_categorias = models.JSONField(
        null=True,
        blank=True,
        help_text="Categorias e análise identificada pela IA"
    )

    lgpd_aceito = models.BooleanField(default=False)
    lgpd_aceito_em = models.DateTimeField()

    class Meta:
        db_table = 'responses_survey_response'
        verbose_name = 'Resposta'
        verbose_name_plural = 'Respostas'
        indexes = [
            models.Index(fields=['campaign', 'created_at']),
            models.Index(fields=['campaign', 'unidade']),
            models.Index(fields=['campaign', 'setor']),
        ]

    def __str__(self):
        return f"{self.campaign.nome} - {self.setor.nome}"
