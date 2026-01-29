from django.urls import path
from .views import (
    DashboardView,
    SectorAnalysisView,
    GenerateSectorAnalysisView,
    SectorAnalysisListView,
    CampaignComparisonView,
    ExportCampaignComparisonView
)

app_name = 'analytics'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('sector-analysis/', SectorAnalysisListView.as_view(), name='sector_analysis_list'),
    path('sector-analysis/<int:setor_id>/<int:campaign_id>/', SectorAnalysisView.as_view(), name='sector_analysis'),
    path('sector-analysis/generate/', GenerateSectorAnalysisView.as_view(), name='generate_sector_analysis'),
    path('campaign-comparison/', CampaignComparisonView.as_view(), name='campaign_comparison'),
    path('campaign-comparison/export/', ExportCampaignComparisonView.as_view(), name='export_campaign_comparison'),
]
