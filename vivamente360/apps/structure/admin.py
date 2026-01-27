from django.contrib import admin
from .models import Unidade, Setor, Cargo


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'codigo', 'ativo', 'created_at']
    list_filter = ['empresa', 'ativo']
    search_fields = ['nome', 'codigo']


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'unidade', 'codigo', 'ativo', 'created_at']
    list_filter = ['unidade__empresa', 'ativo']
    search_fields = ['nome', 'codigo']


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'nivel', 'ativo', 'created_at']
    list_filter = ['empresa', 'ativo']
    search_fields = ['nome', 'nivel']
