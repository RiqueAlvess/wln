from django.contrib import admin
from .models import AnonymousReport, ReportResponse, ReportFollowUp


class ReportResponseInline(admin.TabularInline):
    model = ReportResponse
    extra = 0
    readonly_fields = ['created_at']


class ReportFollowUpInline(admin.TabularInline):
    model = ReportFollowUp
    extra = 0
    readonly_fields = ['created_at']


@admin.register(AnonymousReport)
class AnonymousReportAdmin(admin.ModelAdmin):
    list_display = ['protocolo', 'categoria', 'gravidade', 'status', 'empresa', 'reported_at']
    list_filter = ['status', 'categoria', 'gravidade', 'empresa']
    search_fields = ['protocolo', 'titulo']
    readonly_fields = ['protocolo', 'access_token_hash', 'reported_at']
    inlines = [ReportResponseInline, ReportFollowUpInline]
