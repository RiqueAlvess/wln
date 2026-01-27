from django.contrib import admin
from .models import ChecklistEtapa, PlanoAcao, Evidencia


@admin.register(ChecklistEtapa)
class ChecklistEtapaAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'campaign', 'etapa', 'item_ordem', 'concluido', 'responsavel']
    list_filter = ['empresa', 'campaign', 'etapa', 'concluido']
    search_fields = ['item_texto', 'responsavel']


@admin.register(PlanoAcao)
class PlanoAcaoAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'campaign', 'dimensao', 'nivel_risco', 'responsavel', 'prazo', 'status']
    list_filter = ['empresa', 'campaign', 'dimensao', 'nivel_risco', 'status']
    search_fields = ['descricao_risco', 'acao_proposta', 'responsavel']
    date_hierarchy = 'prazo'


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'campaign', 'tipo', 'uploaded_by', 'created_at']
    list_filter = ['empresa', 'campaign', 'tipo']
    search_fields = ['descricao']
    date_hierarchy = 'created_at'
