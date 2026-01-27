from django.contrib import admin
from .models import UserProfile, AuditLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'telefone', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['empresas', 'unidades_permitidas', 'setores_permitidos']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'empresa', 'acao', 'ip_address', 'created_at']
    list_filter = ['acao', 'empresa']
    search_fields = ['user__username', 'descricao']
    date_hierarchy = 'created_at'
    readonly_fields = ['user', 'empresa', 'acao', 'descricao', 'ip_address', 'user_agent', 'created_at']
