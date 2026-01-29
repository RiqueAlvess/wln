from django.contrib import admin
from .models import PlanoAcao


@admin.register(PlanoAcao)
class PlanoAcaoAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'campaign', 'dimensao', 'nivel_risco', 'responsavel', 'prazo', 'status']
    list_filter = ['empresa', 'campaign', 'dimensao', 'nivel_risco', 'status']
    search_fields = ['descricao_risco', 'acao_proposta', 'responsavel']
    date_hierarchy = 'prazo'
