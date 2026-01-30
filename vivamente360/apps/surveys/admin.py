from django.contrib import admin
from .models import (
    Dimensao,
    Pergunta,
    Campaign,
    CategoriaFatorRisco,
    FatorRisco,
    SeveridadePorCNAE
)


@admin.register(Dimensao)
class DimensaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo', 'tipo', 'ordem', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'codigo']
    ordering = ['ordem']


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'dimensao', 'texto', 'ativo']
    list_filter = ['dimensao', 'ativo']
    search_fields = ['texto']
    ordering = ['numero']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'status', 'data_inicio', 'data_fim', 'created_at']
    list_filter = ['empresa', 'status']
    search_fields = ['nome']
    date_hierarchy = 'data_inicio'


# ============================================================================
# ADMIN - FATORES DE RISCO PSICOSSOCIAL (NR-1)
# ============================================================================

@admin.register(CategoriaFatorRisco)
class CategoriaFatorRiscoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'icone', 'ordem', 'total_fatores']
    search_fields = ['nome', 'codigo', 'descricao']
    ordering = ['ordem']

    def total_fatores(self, obj):
        return obj.fatores.count()
    total_fatores.short_description = 'Total de Fatores'


class SeveridadePorCNAEInline(admin.TabularInline):
    model = SeveridadePorCNAE
    extra = 1
    fields = ['cnae_secao', 'cnae_divisao', 'severidade_ajustada', 'justificativa']


@admin.register(FatorRisco)
class FatorRiscoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo',
        'nome',
        'categoria',
        'severidade_base',
        'total_dimensoes',
        'ativo'
    ]
    list_filter = ['categoria', 'severidade_base', 'ativo']
    search_fields = ['codigo', 'nome', 'descricao', 'exemplos']  # Necessário para autocomplete
    filter_horizontal = ['dimensoes_hse']
    inlines = [SeveridadePorCNAEInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'categoria', 'nome', 'ativo')
        }),
        ('Descrição', {
            'fields': ('descricao', 'exemplos')
        }),
        ('Análise de Risco', {
            'fields': ('severidade_base', 'consequencias', 'dimensoes_hse')
        }),
    )

    def total_dimensoes(self, obj):
        return obj.dimensoes_hse.count()
    total_dimensoes.short_description = 'Dimensões HSE-IT'


@admin.register(SeveridadePorCNAE)
class SeveridadePorCNAEAdmin(admin.ModelAdmin):
    list_display = [
        'fator_risco',
        'cnae_completo',
        'severidade_ajustada',
        'severidade_base_fator'
    ]
    list_filter = ['cnae_secao', 'severidade_ajustada']
    search_fields = ['fator_risco__codigo', 'fator_risco__nome', 'justificativa']
    autocomplete_fields = ['fator_risco']

    def cnae_completo(self, obj):
        return f"{obj.cnae_secao}{obj.cnae_divisao}" if obj.cnae_divisao else obj.cnae_secao
    cnae_completo.short_description = 'CNAE'

    def severidade_base_fator(self, obj):
        return obj.fator_risco.severidade_base
    severidade_base_fator.short_description = 'Severidade Base'
