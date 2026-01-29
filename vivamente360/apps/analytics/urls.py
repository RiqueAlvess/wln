from django.urls import path
from .views import (
    DashboardView,
    SectorAnalysisView,
    GenerateSectorAnalysisView,
    SectorAnalysisListView
)

app_name = 'analytics'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('sector-analysis/', SectorAnalysisListView.as_view(), name='sector_analysis_list'),
    path('sector-analysis/<int:setor_id>/<int:campaign_id>/', SectorAnalysisView.as_view(), name='sector_analysis'),
    path('sector-analysis/generate/', GenerateSectorAnalysisView.as_view(), name='generate_sector_analysis'),
]
