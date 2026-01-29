from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Artigo


@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    """
    Painel administrativo para gerenciamento de artigos.
    """
    list_display = [
        'titulo',
        'categoria_badge',
        'status_badge',
        'destaque_icon',
        'autor',
        'publicado_em',
        'visualizacoes',
        'created_at',
    ]
    list_filter = ['status', 'categoria', 'destaque', 'publicado_em', 'created_at']
    search_fields = ['titulo', 'resumo', 'conteudo']
    prepopulated_fields = {'slug': ('titulo',)}
    readonly_fields = ['visualizacoes', 'created_at', 'updated_at']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'slug', 'categoria', 'resumo')
        }),
        ('Conteúdo', {
            'fields': ('conteudo', 'imagem_capa')
        }),
        ('Publicação', {
            'fields': ('autor', 'status', 'publicado_em', 'destaque')
        }),
        ('Métricas', {
            'fields': ('visualizacoes',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'publicado_em'
    ordering = ['-publicado_em', '-created_at']

    actions = ['publicar_artigos', 'arquivar_artigos', 'marcar_destaque', 'desmarcar_destaque']

    def categoria_badge(self, obj):
        """Exibe badge colorido da categoria."""
        cores = {
            'nr1': '#0d6efd',
            'saude': '#198754',
            'gestao': '#0dcaf0',
            'dicas': '#ffc107',
            'casos': '#6c757d',
            'novidades': '#dc3545',
        }
        cor = cores.get(obj.categoria, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            cor,
            obj.get_categoria_display()
        )
    categoria_badge.short_description = 'Categoria'

    def status_badge(self, obj):
        """Exibe badge colorido do status."""
        cores = {
            'draft': '#6c757d',
            'published': '#198754',
            'archived': '#dc3545',
        }
        cor = cores.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def destaque_icon(self, obj):
        """Exibe ícone de destaque."""
        if obj.destaque:
            return format_html('<span style="font-size: 18px;">🔥</span>')
        return '-'
    destaque_icon.short_description = 'Destaque'

    def publicar_artigos(self, request, queryset):
        """Action para publicar artigos selecionados."""
        now = timezone.now()
        updated = 0
        for artigo in queryset:
            if artigo.status != 'published':
                artigo.status = 'published'
                if not artigo.publicado_em:
                    artigo.publicado_em = now
                artigo.save()
                updated += 1

        self.message_user(
            request,
            f'{updated} artigo(s) publicado(s) com sucesso.'
        )
    publicar_artigos.short_description = 'Publicar artigos selecionados'

    def arquivar_artigos(self, request, queryset):
        """Action para arquivar artigos selecionados."""
        updated = queryset.update(status='archived')
        self.message_user(
            request,
            f'{updated} artigo(s) arquivado(s) com sucesso.'
        )
    arquivar_artigos.short_description = 'Arquivar artigos selecionados'

    def marcar_destaque(self, request, queryset):
        """Action para marcar artigos como destaque."""
        updated = queryset.update(destaque=True)
        self.message_user(
            request,
            f'{updated} artigo(s) marcado(s) como destaque.'
        )
    marcar_destaque.short_description = 'Marcar como destaque'

    def desmarcar_destaque(self, request, queryset):
        """Action para desmarcar artigos como destaque."""
        updated = queryset.update(destaque=False)
        self.message_user(
            request,
            f'{updated} artigo(s) desmarcado(s) como destaque.'
        )
    desmarcar_destaque.short_description = 'Desmarcar destaque'

    def save_model(self, request, obj, form, change):
        """Define o autor automaticamente se não estiver definido."""
        if not obj.autor:
            obj.autor = request.user
        super().save_model(request, obj, form, change)
