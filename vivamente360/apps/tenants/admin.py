from django.contrib import admin
from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'total_funcionarios', 'ativo', 'created_at']
    list_filter = ['ativo']
    search_fields = ['nome', 'cnpj']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'cnpj', 'total_funcionarios', 'ativo')
        }),
        ('Branding', {
            'fields': ('logo_url', 'favicon_url', 'cor_primaria', 'cor_secundaria', 'cor_fonte', 'nome_app')
        }),
    )
