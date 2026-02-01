"""
Serviço para gerenciamento de arquivos gerados por tasks.
Salva arquivos localmente e fornece URLs para download.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)


class TaskFileStorage:
    """
    Gerencia armazenamento de arquivos gerados por tasks assíncronas.
    """

    @staticmethod
    def get_storage_path():
        """Retorna o diretório base para armazenamento de arquivos de tasks."""
        # Usar MEDIA_ROOT se configurado, senão criar pasta local
        if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
            base_path = Path(settings.MEDIA_ROOT) / 'task_files'
        else:
            base_path = Path(settings.BASE_DIR) / 'media' / 'task_files'

        # Criar diretório se não existir
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path

    @staticmethod
    def save_task_file(file_content, filename, task_id, file_type='general'):
        """
        Salva arquivo gerado por uma task.

        Args:
            file_content: Conteúdo do arquivo (bytes ou BytesIO)
            filename: Nome do arquivo
            task_id: ID da task que gerou o arquivo
            file_type: Tipo de arquivo (export, report, etc)

        Returns:
            dict com informações do arquivo salvo:
                - file_path: Caminho relativo do arquivo
                - file_name: Nome do arquivo
                - file_size: Tamanho em bytes
                - full_path: Caminho absoluto
        """
        try:
            # Criar estrutura de diretórios: task_files/YYYY/MM/tipo/
            now = datetime.now()
            year_month_path = f"{now.year}/{now.month:02d}/{file_type}"

            # Gerar nome único para o arquivo
            file_ext = Path(filename).suffix
            unique_name = f"{task_id}_{uuid.uuid4().hex[:8]}{file_ext}"

            # Caminho relativo
            relative_path = f"task_files/{year_month_path}/{unique_name}"

            # Obter bytes do conteúdo
            if hasattr(file_content, 'getvalue'):
                # É um BytesIO
                file_bytes = file_content.getvalue()
            elif hasattr(file_content, 'read'):
                # É um file-like object
                file_bytes = file_content.read()
            else:
                # Já são bytes
                file_bytes = file_content

            # Salvar arquivo usando Django storage
            saved_path = default_storage.save(relative_path, ContentFile(file_bytes))

            # Obter tamanho
            file_size = len(file_bytes)

            logger.info(f"Arquivo salvo: {saved_path} ({file_size} bytes)")

            return {
                'file_path': saved_path,
                'file_name': filename,
                'file_size': file_size,
                'full_path': default_storage.path(saved_path) if hasattr(default_storage, 'path') else saved_path
            }

        except Exception as e:
            logger.error(f"Erro ao salvar arquivo da task {task_id}: {str(e)}")
            raise

    @staticmethod
    def get_file_url(file_path):
        """
        Retorna URL para download do arquivo.

        Args:
            file_path: Caminho relativo do arquivo

        Returns:
            URL do arquivo
        """
        try:
            return default_storage.url(file_path)
        except Exception as e:
            logger.error(f"Erro ao obter URL do arquivo {file_path}: {str(e)}")
            return None

    @staticmethod
    def delete_task_file(file_path):
        """
        Deleta arquivo de uma task.

        Args:
            file_path: Caminho relativo do arquivo

        Returns:
            True se deletado com sucesso
        """
        try:
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
                logger.info(f"Arquivo deletado: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {file_path}: {str(e)}")
            return False

    @staticmethod
    def cleanup_old_files(days=30):
        """
        Remove arquivos de tasks mais antigos que X dias.

        Args:
            days: Número de dias (padrão: 30)

        Returns:
            Número de arquivos removidos
        """
        from apps.core.models import TaskQueue
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)

        old_tasks = TaskQueue.objects.filter(
            completed_at__lt=cutoff_date,
            file_path__isnull=False
        ).exclude(file_path='')

        deleted_count = 0
        for task in old_tasks:
            if TaskFileStorage.delete_task_file(task.file_path):
                task.file_path = ''
                task.save(update_fields=['file_path'])
                deleted_count += 1

        logger.info(f"Limpeza de arquivos antigos: {deleted_count} arquivos removidos")
        return deleted_count

    @staticmethod
    def get_file_type_from_task_type(task_type):
        """Mapeia tipo de task para tipo de arquivo."""
        mapping = {
            'export_plano_acao': 'plano_acao',
            'export_plano_acao_rich': 'plano_acao',
            'export_checklist_nr1': 'checklist',
            'export_campaign_comparison': 'comparacao',
            'export_risk_matrix_excel': 'matriz_risco',
            'export_pgr_document': 'pgr',
        }
        return mapping.get(task_type, 'general')
