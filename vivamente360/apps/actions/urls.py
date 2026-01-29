from django.urls import path
from .views import (
    PlanoAcaoListView,
    ExportPlanoAcaoWordView
)

app_name = 'actions'

urlpatterns = [
    path('<int:campaign_id>/planos/', PlanoAcaoListView.as_view(), name='planos'),
    path('<int:campaign_id>/planos/export-word/', ExportPlanoAcaoWordView.as_view(), name='export_plano_word'),
]
