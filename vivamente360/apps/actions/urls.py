from django.urls import path
from .views import ChecklistView, PlanoAcaoListView

app_name = 'actions'

urlpatterns = [
    path('<int:campaign_id>/checklist/', ChecklistView.as_view(), name='checklist'),
    path('<int:campaign_id>/planos/', PlanoAcaoListView.as_view(), name='planos'),
]
