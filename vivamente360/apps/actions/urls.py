from django.urls import path
from .views import (
    ChecklistView,
    PlanoAcaoListView,
    EvidenciaListView,
    EvidenciaUploadView,
    EvidenciaDeleteView
)

app_name = 'actions'

urlpatterns = [
    path('<int:campaign_id>/checklist/', ChecklistView.as_view(), name='checklist'),
    path('<int:campaign_id>/planos/', PlanoAcaoListView.as_view(), name='planos'),
    path('<int:campaign_id>/evidencias/', EvidenciaListView.as_view(), name='evidencias'),
    path('<int:campaign_id>/evidencias/upload/', EvidenciaUploadView.as_view(), name='evidencia_upload'),
    path('evidencias/<int:pk>/delete/', EvidenciaDeleteView.as_view(), name='evidencia_delete'),
]
