from django.urls import path
from .views import HomeView, test_404, test_500, test_403, test_400

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    # URLs para teste de páginas de erro (apenas em desenvolvimento)
    path('test/404/', test_404, name='test_404'),
    path('test/500/', test_500, name='test_500'),
    path('test/403/', test_403, name='test_403'),
    path('test/400/', test_400, name='test_400'),
]
