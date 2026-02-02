"""
API Views para Tasks e Notificações
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters

from .models import TaskQueue, UserNotification
from .serializers import (
    TaskQueueSerializer,
    UserNotificationSerializer,
    NotificationMarkReadSerializer
)
import logging

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Paginação padrão para as APIs."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskQueueFilter(filters.FilterSet):
    """Filtro para TaskQueue."""
    status = filters.CharFilter(field_name='status')
    task_type = filters.CharFilter(field_name='task_type')
    is_file_task = filters.BooleanFilter(method='filter_is_file_task')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = TaskQueue
        fields = ['status', 'task_type', 'is_file_task']

    def filter_is_file_task(self, queryset, name, value):
        """Filtra tasks que geram arquivos."""
        file_task_types = [
            'export_plano_acao',
            'export_plano_acao_rich',
            'export_checklist_nr1',
            'export_campaign_comparison',
            'export_risk_matrix_excel',
            'export_pgr_document',
        ]
        if value:
            return queryset.filter(task_type__in=file_task_types)
        else:
            return queryset.exclude(task_type__in=file_task_types)


@method_decorator(csrf_exempt, name='dispatch')
class TaskQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consulta de tasks.
    Somente leitura - tasks são criadas por outros endpoints.
    CSRF exemption aplicado para compatibilidade com chamadas AJAX.
    """
    serializer_class = TaskQueueSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TaskQueueFilter
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['created_at', 'completed_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Retorna tasks do usuário logado."""
        user = self.request.user
        queryset = TaskQueue.objects.filter(user=user)

        # Se usuário tem empresa, filtrar também por empresa
        if hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Retorna resumo das tasks do usuário.
        """
        queryset = self.get_queryset()

        summary = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'processing': queryset.filter(status='processing').count(),
            'completed': queryset.filter(status='completed').count(),
            'failed': queryset.filter(status='failed').count(),
            'files_available': queryset.filter(
                status='completed',
                file_path__isnull=False
            ).exclude(file_path='').count(),
        }

        return Response(summary)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download de arquivo gerado por uma task.
        """
        task = self.get_object()

        # Verificar se task tem arquivo disponível
        if not task.can_download:
            return Response(
                {'error': 'Arquivo não disponível para download'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Verificar se arquivo existe
            if not default_storage.exists(task.file_path):
                logger.error(f"Arquivo não encontrado: {task.file_path}")
                return Response(
                    {'error': 'Arquivo não encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Abrir arquivo para download
            file_obj = default_storage.open(task.file_path, 'rb')

            # Determinar content type baseado na extensão
            content_types = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.csv': 'text/csv',
                '.txt': 'text/plain',
            }

            import os
            ext = os.path.splitext(task.file_name)[1].lower()
            content_type = content_types.get(ext, 'application/octet-stream')

            response = FileResponse(file_obj, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{task.file_name}"'
            response['Content-Length'] = task.file_size

            return response

        except Exception as e:
            logger.error(f"Erro ao fazer download do arquivo {task.file_path}: {str(e)}")
            return Response(
                {'error': 'Erro ao baixar arquivo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'])
    def delete_file(self, request, pk=None):
        """
        Deleta arquivo de uma task completada.
        """
        task = self.get_object()

        if not task.file_path:
            return Response(
                {'error': 'Task não possui arquivo associado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from services.task_file_storage import TaskFileStorage
            if TaskFileStorage.delete_task_file(task.file_path):
                task.file_path = ''
                task.file_name = ''
                task.file_size = None
                task.save(update_fields=['file_path', 'file_name', 'file_size'])

                return Response({'message': 'Arquivo deletado com sucesso'})
            else:
                return Response(
                    {'error': 'Arquivo não encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo: {str(e)}")
            return Response(
                {'error': 'Erro ao deletar arquivo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class UserNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para notificações do usuário.
    CSRF exemption aplicado para compatibilidade com chamadas AJAX.
    """
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    ordering = ['-created_at']

    def get_queryset(self):
        """Retorna notificações ativas do usuário logado (últimas 24h)."""
        return UserNotification.objects.active().filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Retorna número de notificações não lidas.
        """
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Retorna todas as notificações não lidas.
        """
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Marca uma notificação como lida.
        """
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Marca todas as notificações como lidas.
        """
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'message': f'{updated} notificações marcadas como lidas'})

    @action(detail=False, methods=['post'])
    def mark_multiple_read(self, request):
        """
        Marca múltiplas notificações como lidas.
        """
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data['notification_ids']

        if not notification_ids:
            # Se lista vazia, marcar todas como lidas
            return self.mark_all_read(request)

        updated = self.get_queryset().filter(
            id__in=notification_ids,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        return Response({'message': f'{updated} notificações marcadas como lidas'})

    @action(detail=False, methods=['delete'])
    def clear_read(self, request):
        """
        Deleta todas as notificações já lidas.
        """
        deleted, _ = self.get_queryset().filter(is_read=True).delete()
        return Response({'message': f'{deleted} notificações deletadas'})
