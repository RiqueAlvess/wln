from django.contrib import admin
from .models import SurveyInvitation


@admin.register(SurveyInvitation)
class SurveyInvitationAdmin(admin.ModelAdmin):
    list_display = ['hash_token', 'campaign', 'unidade', 'setor', 'status', 'created_at']
    list_filter = ['status', 'campaign', 'empresa']
    search_fields = ['hash_token']
    readonly_fields = ['hash_token', 'email_encrypted', 'nome_encrypted']
    date_hierarchy = 'created_at'
