from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField

from apps.core.models import TimeStampedModel


class Artigo(TimeStampedModel):
    """
    Modelo para artigos e newsletters do sistema Vivamente 360º.
    Permite ao admin publicar conteúdo educativo sobre NR-1, saúde mental,
    gestão de pessoas e dicas práticas.
    """

    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('published', 'Publicado'),
        ('archived', 'Arquivado'),
    ]

    CATEGORIAS = [
        ('nr1', 'NR-1 e Compliance'),
        ('saude', 'Saúde Mental'),
        ('gestao', 'Gestão de Pessoas'),
        ('dicas', 'Dicas Práticas'),
        ('casos', 'Casos de Sucesso'),
        ('novidades', 'Novidades do Sistema'),
    ]

    # Informações básicas
    titulo = models.CharField(
        max_length=255,
        verbose_name='Título',
        help_text='Título principal do artigo'
    )
    slug = models.SlugField(
        unique=True,
        max_length=255,
        verbose_name='Slug',
        help_text='URL amigável (gerado automaticamente do título)'
    )
    resumo = models.TextField(
        max_length=500,
        verbose_name='Resumo',
        help_text='Texto exibido no card de prévia (máx. 500 caracteres)'
    )
    conteudo = RichTextUploadingField(
        verbose_name='Conteúdo',
        help_text='Conteúdo completo do artigo com formatação rica',
        config_name='awesome_ckeditor'
    )

    # Imagem
    imagem_capa = models.ImageField(
        upload_to='artigos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Imagem de Capa',
        help_text='Imagem principal do artigo'
    )

    # Autoria e status
    autor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='artigos',
        verbose_name='Autor',
        help_text='Usuário que criou o artigo'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
        help_text='Status de publicação do artigo'
    )

    # Publicação
    publicado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Publicado em',
        help_text='Data e hora de publicação'
    )
    destaque = models.BooleanField(
        default=False,
        verbose_name='Em Destaque',
        help_text='Exibir artigo em destaque na página principal'
    )

    # Categorização
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIAS,
        verbose_name='Categoria',
        help_text='Categoria do artigo'
    )

    # Métricas (futuro)
    visualizacoes = models.PositiveIntegerField(
        default=0,
        verbose_name='Visualizações',
        help_text='Número de visualizações do artigo'
    )

    class Meta:
        ordering = ['-publicado_em', '-created_at']
        verbose_name = 'Artigo'
        verbose_name_plural = 'Artigos'
        indexes = [
            models.Index(fields=['-publicado_em']),
            models.Index(fields=['status', 'categoria']),
            models.Index(fields=['destaque', 'status']),
        ]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        """
        Override save para gerar slug automaticamente e definir data de publicação.
        """
        # Gerar slug se não existir
        if not self.slug:
            self.slug = slugify(self.titulo)
            # Garantir slug único
            original_slug = self.slug
            counter = 1
            while Artigo.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1

        # Definir data de publicação quando status mudar para 'published'
        if self.status == 'published' and not self.publicado_em:
            self.publicado_em = timezone.now()

        # Limpar data de publicação se voltar para rascunho
        if self.status == 'draft':
            self.publicado_em = None

        super().save(*args, **kwargs)

    @property
    def get_categoria_display_class(self):
        """Retorna a classe CSS para a categoria."""
        categoria_classes = {
            'nr1': 'primary',
            'saude': 'success',
            'gestao': 'info',
            'dicas': 'warning',
            'casos': 'secondary',
            'novidades': 'danger',
        }
        return categoria_classes.get(self.categoria, 'secondary')

    def incrementar_visualizacao(self):
        """Incrementa o contador de visualizações."""
        self.visualizacoes += 1
        self.save(update_fields=['visualizacoes'])
