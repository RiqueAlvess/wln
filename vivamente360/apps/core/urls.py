from django.urls import path
from .views import HomeView, LGPDComplianceView

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('lgpd-compliance/', LGPDComplianceView.as_view(), name='lgpd_compliance'),
]
