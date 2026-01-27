from django.urls import path
from .views import ImportCSVView, ManageInvitationsView, DispatchEmailsView

app_name = 'invitations'

urlpatterns = [
    path('<int:campaign_id>/manage/', ManageInvitationsView.as_view(), name='manage'),
    path('<int:campaign_id>/import/', ImportCSVView.as_view(), name='import'),
    path('<int:campaign_id>/dispatch/', DispatchEmailsView.as_view(), name='dispatch'),
]
