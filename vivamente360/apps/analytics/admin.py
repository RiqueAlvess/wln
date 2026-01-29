from django.contrib import admin
from .models import SectorAnalysis


@admin.register(SectorAnalysis)
class SectorAnalysisAdmin(admin.ModelAdmin):
    list_display = ['setor', 'campaign', 'empresa', 'status', 'total_respostas', 'created_at']
    list_filter = ['status', 'empresa', 'campaign', 'created_at']
    search_fields = ['setor__nome', 'empresa__nome', 'campaign__nome']
    readonly_fields = ['created_at', 'updated_at', 'generated_by']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'setor', 'campaign', 'status')
        }),
        ('Análise', {
            'fields': ('diagnostico', 'fatores_contribuintes', 'pontos_atencao', 'pontos_fortes',
                      'recomendacoes', 'impacto_esperado', 'alertas_sentimento')
        }),
        ('Metadados', {
            'fields': ('total_respostas', 'scores', 'generated_by', 'error_message',
                      'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Não permitir adicionar manualmente via admin
        return False
