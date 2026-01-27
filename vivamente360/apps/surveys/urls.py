from django.urls import path
from .views import CampaignListView, CampaignCreateView, CampaignDetailView

app_name = 'surveys'

urlpatterns = [
    path('', CampaignListView.as_view(), name='list'),
    path('create/', CampaignCreateView.as_view(), name='create'),
    path('<int:pk>/', CampaignDetailView.as_view(), name='detail'),
]
