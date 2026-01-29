from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlanoAcaoListView,
    ExportPlanoAcaoWordView,
    ChecklistNR1ListView,
    ChecklistNR1ItemUpdateView,
    EvidenciaNR1UploadView,
    EvidenciaNR1DeleteView,
    ChecklistNR1ExportPDFView,
    ChecklistNR1ViewSet,
    EvidenciaNR1ViewSet
)

# Router para API REST
router = DefaultRouter()
router.register(r'checklist-nr1', ChecklistNR1ViewSet, basename='checklist-nr1-api')
router.register(r'evidencias-nr1', EvidenciaNR1ViewSet, basename='evidencias-nr1-api')

app_name = 'actions'

urlpatterns = [
    # Planos de Ação
    path('<int:campaign_id>/planos/', PlanoAcaoListView.as_view(), name='planos'),
    path('<int:campaign_id>/planos/export-word/', ExportPlanoAcaoWordView.as_view(), name='export_plano_word'),

    # Checklist NR-1
    path('<int:campaign_id>/checklist-nr1/', ChecklistNR1ListView.as_view(), name='checklist_nr1'),
    path('checklist-nr1/item/<int:item_id>/update/', ChecklistNR1ItemUpdateView.as_view(), name='checklist_nr1_item_update'),
    path('checklist-nr1/item/<int:item_id>/upload-evidencia/', EvidenciaNR1UploadView.as_view(), name='evidencia_nr1_upload'),
    path('evidencia-nr1/<int:evidencia_id>/delete/', EvidenciaNR1DeleteView.as_view(), name='evidencia_nr1_delete'),
    path('<int:campaign_id>/checklist-nr1/export-pdf/', ChecklistNR1ExportPDFView.as_view(), name='checklist_nr1_export_pdf'),

    # API REST
    path('api/', include(router.urls)),
]
