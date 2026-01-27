from django.contrib import admin
from .models import SurveyResponse


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'unidade', 'setor', 'cargo', 'faixa_etaria', 'created_at']
    list_filter = ['campaign', 'unidade', 'setor', 'faixa_etaria', 'genero']
    readonly_fields = ['campaign', 'unidade', 'setor', 'cargo', 'faixa_etaria', 'tempo_empresa', 'genero', 'respostas', 'lgpd_aceito', 'lgpd_aceito_em', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
