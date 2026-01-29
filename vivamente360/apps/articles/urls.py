"""
URLs para o app de artigos.
"""
from django.urls import path

from .views import ArtigoListView, ArtigoDetailView

app_name = 'articles'

urlpatterns = [
    path('', ArtigoListView.as_view(), name='list'),
    path('<slug:slug>/', ArtigoDetailView.as_view(), name='detail'),
]
