from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimeStampedModel
from apps.tenants.models import Empresa
from apps.surveys.models import Campaign, Dimensao

User = get_user_model()


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

    # Campos para editor de texto rico (TipTap)
    conteudo_estruturado = models.JSONField(
        null=True,
        blank=True,
        help_text="Conteúdo do editor TipTap em formato JSON"
    )
    conteudo_html = models.TextField(
        blank=True,
        help_text="HTML renderizado do plano de ação para exportação"
    )

    class Meta:
        db_table = 'actions_plano_acao'
        verbose_name = 'Plano de Ação'
        verbose_name_plural = 'Planos de Ação'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.dimensao.nome} - {self.nivel_risco}"


class ChecklistNR1Etapa(TimeStampedModel):
    """
    Modelo para gerenciar as etapas do checklist de compliance NR-1.
    Cada item representa uma tarefa específica dentro de uma das 6 etapas.
    """
    ETAPAS = [
        (1, "Preparação"),
        (2, "Identificação de Perigos"),
        (3, "Avaliação de Riscos"),
        (4, "Planejamento e Controle"),
        (5, "Monitoramento e Revisão"),
        (6, "Comunicação e Cultura"),
    ]

    # Relacionamentos
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='checklist_nr1_items'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='checklist_nr1_items'
    )

    # Dados da etapa
    etapa = models.IntegerField(choices=ETAPAS)
    item_texto = models.TextField(help_text="Descrição da tarefa do checklist")
    item_ordem = models.IntegerField(help_text="Ordem do item dentro da etapa")

    # Status
    concluido = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(blank=True, null=True)

    # Gestão
    responsavel = models.CharField(max_length=255, blank=True)
    prazo = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True)

    # Automático (não requer ação manual)
    automatico = models.BooleanField(default=False, help_text="Item preenchido automaticamente pelo sistema")

    class Meta:
        db_table = 'actions_checklist_nr1_etapa'
        verbose_name = 'Item de Checklist NR-1'
        verbose_name_plural = 'Itens de Checklist NR-1'
        ordering = ['etapa', 'item_ordem']
        unique_together = [['campaign', 'etapa', 'item_ordem']]

    def __str__(self):
        return f"Etapa {self.etapa} - Item {self.item_ordem}: {self.item_texto[:50]}"

    def get_progresso_etapa(self):
        """Calcula o progresso percentual da etapa"""
        itens_etapa = ChecklistNR1Etapa.objects.filter(
            campaign=self.campaign,
            etapa=self.etapa
        )
        total = itens_etapa.count()
        concluidos = itens_etapa.filter(concluido=True).count()
        return (concluidos / total * 100) if total > 0 else 0


class EvidenciaNR1(TimeStampedModel):
    """
    Modelo para gerenciar evidências anexadas aos itens do checklist NR-1.
    Suporta diversos tipos de documentos para comprovação de compliance.
    """
    TIPOS_PERMITIDOS = [
        ('documento', 'Documento (PDF, DOC, DOCX)'),
        ('imagem', 'Imagem (JPG, PNG)'),
        ('planilha', 'Planilha (XLS, XLSX, CSV)'),
        ('apresentacao', 'Apresentação (PPT, PPTX)'),
        ('email', 'E-mail/Comunicado'),
        ('ata', 'Ata de Reunião'),
        ('certificado', 'Certificado/Treinamento'),
        ('outro', 'Outro'),
    ]

    # Relacionamentos
    checklist_item = models.ForeignKey(
        ChecklistNR1Etapa,
        on_delete=models.CASCADE,
        related_name='evidencias'
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='evidencias_nr1'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='evidencias_nr1'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evidencias_nr1_uploaded'
    )

    # Arquivo
    arquivo = models.FileField(
        upload_to='evidencias_nr1/%Y/%m/',
        help_text="Upload do arquivo de evidência"
    )
    nome_original = models.CharField(
        max_length=255,
        help_text="Nome original do arquivo"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_PERMITIDOS,
        default='outro'
    )
    tamanho_bytes = models.BigIntegerField(
        default=0,
        help_text="Tamanho do arquivo em bytes"
    )

    # Metadados
    descricao = models.TextField(
        blank=True,
        help_text="Descrição da evidência"
    )

    class Meta:
        db_table = 'actions_evidencia_nr1'
        verbose_name = 'Evidência NR-1'
        verbose_name_plural = 'Evidências NR-1'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nome_original} ({self.get_tipo_display()})"

    def get_tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado"""
        bytes_size = self.tamanho_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"

    @property
    def extensao(self):
        """Retorna a extensão do arquivo"""
        return self.nome_original.split('.')[-1].lower() if '.' in self.nome_original else ''
