from django.contrib import admin
from .models import PlanoAcao, ChecklistNR1Etapa, EvidenciaNR1


@admin.register(PlanoAcao)
class PlanoAcaoAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'campaign', 'dimensao', 'nivel_risco', 'responsavel', 'prazo', 'status']
    list_filter = ['empresa', 'campaign', 'dimensao', 'nivel_risco', 'status']
    search_fields = ['descricao_risco', 'acao_proposta', 'responsavel']
    date_hierarchy = 'prazo'


@admin.register(ChecklistNR1Etapa)
class ChecklistNR1EtapaAdmin(admin.ModelAdmin):
    list_display = ['etapa', 'item_ordem', 'item_texto_curto', 'campaign', 'empresa', 'concluido', 'responsavel', 'prazo', 'automatico']
    list_filter = ['etapa', 'concluido', 'automatico', 'empresa', 'campaign']
    search_fields = ['item_texto', 'responsavel', 'observacoes']
    date_hierarchy = 'prazo'
    ordering = ['campaign', 'etapa', 'item_ordem']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('campaign', 'empresa', 'etapa', 'item_ordem', 'item_texto', 'automatico')
        }),
        ('Status', {
            'fields': ('concluido', 'data_conclusao')
        }),
        ('Gestão', {
            'fields': ('responsavel', 'prazo', 'observacoes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def item_texto_curto(self, obj):
        return obj.item_texto[:50] + '...' if len(obj.item_texto) > 50 else obj.item_texto
    item_texto_curto.short_description = 'Item'


@admin.register(EvidenciaNR1)
class EvidenciaNR1Admin(admin.ModelAdmin):
    list_display = ['nome_original', 'tipo', 'checklist_item_info', 'campaign', 'empresa', 'uploaded_by', 'tamanho_formatado_display', 'created_at']
    list_filter = ['tipo', 'empresa', 'campaign', 'created_at']
    search_fields = ['nome_original', 'descricao', 'checklist_item__item_texto']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'tamanho_bytes', 'nome_original', 'uploaded_by']
    ordering = ['-created_at']

    fieldsets = (
        ('Arquivo', {
            'fields': ('arquivo', 'nome_original', 'tipo', 'tamanho_bytes')
        }),
        ('Vinculação', {
            'fields': ('checklist_item', 'campaign', 'empresa')
        }),
        ('Metadados', {
            'fields': ('descricao', 'uploaded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def checklist_item_info(self, obj):
        return f"Etapa {obj.checklist_item.etapa} - Item {obj.checklist_item.item_ordem}"
    checklist_item_info.short_description = 'Item do Checklist'

    def tamanho_formatado_display(self, obj):
        return obj.get_tamanho_formatado()
    tamanho_formatado_display.short_description = 'Tamanho'
