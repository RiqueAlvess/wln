from django.contrib import admin
from .models import Dimensao, Pergunta, Campaign


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
