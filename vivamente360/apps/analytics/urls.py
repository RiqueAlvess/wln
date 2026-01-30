from django.urls import path
from .views import (
    DashboardView,
    SectorAnalysisView,
    GenerateSectorAnalysisView,
    SectorAnalysisListView,
    CampaignComparisonView,
    ExportCampaignComparisonView,
    # Matriz de Risco Psicossocial NR-1
    PsychosocialRiskMatrixView,
    SectorRiskDetailView,
    ExportRiskMatrixExcelView,
    ExportRiskMatrixPGRView,
)

app_name = 'analytics'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('sector-analysis/', SectorAnalysisListView.as_view(), name='sector_analysis_list'),
    path('sector-analysis/<int:setor_id>/<int:campaign_id>/', SectorAnalysisView.as_view(), name='sector_analysis'),
    path('sector-analysis/generate/', GenerateSectorAnalysisView.as_view(), name='generate_sector_analysis'),
    path('campaign-comparison/', CampaignComparisonView.as_view(), name='campaign_comparison'),
    path('campaign-comparison/export/', ExportCampaignComparisonView.as_view(), name='export_campaign_comparison'),

    # Matriz de Risco Psicossocial NR-1
    path('psychosocial-risk/', PsychosocialRiskMatrixView.as_view(), name='psychosocial_risk_matrix'),
    path('psychosocial-risk/sector/<int:setor_id>/<int:campaign_id>/', SectorRiskDetailView.as_view(), name='sector_risk_detail'),
    path('psychosocial-risk/export/excel/<int:campaign_id>/', ExportRiskMatrixExcelView.as_view(), name='export_risk_matrix_excel'),
    path('psychosocial-risk/export/pgr/<int:campaign_id>/', ExportRiskMatrixPGRView.as_view(), name='export_risk_matrix_pgr'),
]
