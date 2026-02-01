from django.utils import timezone
from apps.core.models import TaskQueue
from apps.analytics.models import SectorAnalysis
from services.sector_analysis_service import SectorAnalysisService
import logging

logger = logging.getLogger(__name__)


def process_sector_analysis_queue():
    """Processa fila de análises de setor por IA"""

    # Buscar próxima task pendente
    task = TaskQueue.objects.filter(
        task_type='generate_sector_analysis',
        status='pending'
    ).first()

    if not task:
        return False

    # Marcar como processando
    task.status = 'processing'
    task.started_at = timezone.now()
    task.attempts += 1
    task.save()

    try:
        # Extrair parâmetros
        setor_id = task.payload['setor_id']
        campaign_id = task.payload['campaign_id']
        user_id = task.payload.get('user_id')

        logger.info(f"Processando análise IA para setor {setor_id}, campanha {campaign_id}")

        # Gerar análise usando service
        analysis = SectorAnalysisService.gerar_analise(setor_id, campaign_id)

        # Marcar como concluído
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.payload['analysis_id'] = analysis.id
        task.save()

        logger.info(f"Análise gerada com sucesso: ID {analysis.id}")
        return True

    except Exception as e:
        logger.error(f"Erro ao processar análise: {str(e)}")
        task.error_message = str(e)

        if task.attempts >= task.max_attempts:
            task.status = 'failed'
        else:
            task.status = 'pending'  # Retry

        task.save()
        return False


def enqueue_sector_analysis(setor_id, campaign_id, user_id=None):
    """Enfileira análise de setor para processamento em background"""

    task = TaskQueue.objects.create(
        task_type='generate_sector_analysis',
        payload={
            'setor_id': setor_id,
            'campaign_id': campaign_id,
            'user_id': user_id
        },
        max_attempts=3
    )

    logger.info(f"Análise enfileirada: Task ID {task.id}")
    return task
