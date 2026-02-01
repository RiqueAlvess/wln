from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HomeView, TaskProcessingView, test_404, test_500, test_403, test_400
from .api_views import TaskQueueViewSet, UserNotificationViewSet

app_name = 'core'

# Router para APIs
router = DefaultRouter()
router.register(r'tasks', TaskQueueViewSet, basename='task')
router.register(r'notifications', UserNotificationViewSet, basename='notification')

urlpatterns = [
    path('', HomeView.as_view(), name='home'),

    # Tela de processamento de tasks
    path('tasks/processing/', TaskProcessingView.as_view(), name='task_processing'),

    # API Routes
    path('api/', include(router.urls)),

    # URLs para teste de páginas de erro (apenas em desenvolvimento)
    path('test/404/', test_404, name='test_404'),
    path('test/500/', test_500, name='test_500'),
    path('test/403/', test_403, name='test_403'),
    path('test/400/', test_400, name='test_400'),
]
