from django.urls import path
from .views import (
    ReportCreateView,
    ReportTrackView,
    ReportFollowUpView,
    ReportListView,
    ReportDetailView,
    ReportRespondView,
)

app_name = 'reports'

urlpatterns = [
    # URLs públicas (anônimas) - NÃO requerem autenticação
    path('<slug:empresa_slug>/new/', ReportCreateView.as_view(), name='create'),
    path('<slug:empresa_slug>/track/', ReportTrackView.as_view(), name='track'),
    path('<slug:empresa_slug>/followup/', ReportFollowUpView.as_view(), name='followup'),

    # URLs do RH - Requerem autenticação e papel RH
    path('manage/', ReportListView.as_view(), name='rh_list'),
    path('manage/<int:report_id>/', ReportDetailView.as_view(), name='rh_detail'),
    path('manage/<int:report_id>/respond/', ReportRespondView.as_view(), name='rh_respond'),
]
