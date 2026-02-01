"""
Processadores de tarefas para o sistema de filas em banco de dados.
Todas as tarefas são enfileiradas no modelo TaskQueue e processadas por workers.

Tipos de tasks suportadas:
- send_email: Envio de e-mails (convites, notificações)
- generate_sector_analysis: Análise de setor por IA (GPT-4o)
- import_csv: Importação de dados CSV
- export_plano_acao: Exportação de planos de ação (Word)
- export_plano_acao_rich: Exportação de plano de ação detalhado (Word)
- export_checklist_nr1: Exportação de checklist NR-1 (PDF)
- export_campaign_comparison: Comparação de campanhas (Word)
- export_risk_matrix_excel: Matriz de risco (Excel)
"""
from django.utils import timezone
from django.db.models import F
from apps.core.models import TaskQueue
from services.export_service import ExportService
from services.import_service import ImportService
from services.crypto_service import CryptoService
from apps.surveys.models import Campaign
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Processador base para tarefas do sistema."""

    @staticmethod
    def process_task(task):
        """
        Processa uma tarefa baseada no task_type.
        Retorna True se processou com sucesso, False caso contrário.
        """
        task.status = 'processing'
        task.started_at = timezone.now()
        task.attempts += 1
        task.save()

        try:
            # Dispatch baseado no tipo de tarefa
            if task.task_type == 'send_email':
                result = TaskProcessor._process_send_email(task)
            elif task.task_type == 'generate_sector_analysis':
                result = TaskProcessor._process_sector_analysis(task)
            elif task.task_type == 'import_csv':
                result = TaskProcessor._process_import_csv(task)
            elif task.task_type == 'export_plano_acao':
                result = TaskProcessor._process_export_plano_acao(task)
            elif task.task_type == 'export_plano_acao_rich':
                result = TaskProcessor._process_export_plano_acao_rich(task)
            elif task.task_type == 'export_checklist_nr1':
                result = TaskProcessor._process_export_checklist_nr1(task)
            elif task.task_type == 'export_campaign_comparison':
                result = TaskProcessor._process_export_campaign_comparison(task)
            elif task.task_type == 'export_risk_matrix_excel':
                result = TaskProcessor._process_export_risk_matrix_excel(task)
            else:
                logger.warning(f"Tipo de tarefa desconhecido: {task.task_type}")
                task.status = 'failed'
                task.error_message = f"Tipo de tarefa não suportado: {task.task_type}"
                task.save()
                return False

            # Marcar como concluída
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.payload['result'] = result
            task.save()

            logger.info(f"Tarefa {task.id} ({task.task_type}) processada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao processar tarefa {task.id} ({task.task_type}): {str(e)}")
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
            return False

    @staticmethod
    def _process_send_email(task):
        """Processa envio de e-mail."""
        from services.email_service import get_email_service
        from apps.invitations.models import SurveyInvitation

        payload = task.payload
        email_service = get_email_service()

        success = email_service.send(
            to=payload['to'],
            subject=payload['subject'],
            html_body=payload['html']
        )

        if not success:
            raise Exception("Falha no envio de e-mail")

        # Atualizar status do convite
        if 'invitation_id' in payload:
            SurveyInvitation.objects.filter(
                id=payload['invitation_id']
            ).update(status='sent', sent_at=timezone.now())

        return {'success': True, 'email_sent': True}

    @staticmethod
    def _process_sector_analysis(task):
        """Processa análise de setor por IA."""
        from services.sector_analysis_service import SectorAnalysisService

        payload = task.payload
        setor_id = payload['setor_id']
        campaign_id = payload['campaign_id']

        logger.info(f"Processando análise IA para setor {setor_id}, campanha {campaign_id}")

        # Gerar análise usando service
        analysis = SectorAnalysisService.gerar_analise(setor_id, campaign_id)

        if not analysis:
            raise Exception("Falha ao gerar análise de setor")

        logger.info(f"Análise gerada com sucesso: ID {analysis.id}")
        return {'success': True, 'analysis_id': analysis.id}

    @staticmethod
    def _process_import_csv(task):
        """Processa importação de CSV."""
        payload = task.payload
        campaign_id = payload['campaign_id']
        rows = payload['rows']

        campaign = Campaign.objects.get(id=campaign_id)
        crypto_service = CryptoService()

        result = ImportService.process_import(
            campaign.empresa,
            campaign,
            rows,
            crypto_service
        )

        return {
            'created': result['created'],
            'errors': result['errors'][:10]  # Limitar erros no payload
        }

    @staticmethod
    def _process_export_plano_acao(task):
        """Processa exportação de plano de ação."""
        from apps.actions.models import PlanoAcao

        payload = task.payload
        campaign_id = payload['campaign_id']
        plano_ids = payload.get('plano_ids', [])

        campaign = Campaign.objects.get(id=campaign_id)
        planos = PlanoAcao.objects.filter(id__in=plano_ids)

        doc = ExportService.export_plano_acao_word(campaign, planos)

        # Salvar documento em memória para obter tamanho
        buffer = BytesIO()
        doc.save(buffer)
        file_size = buffer.tell()
        buffer.close()

        # TODO: Salvar arquivo em storage permanente (S3, filesystem, etc)
        # e retornar URL ou caminho

        return {
            'success': True,
            'file_size': file_size,
            'filename': f'plano_acao_{campaign_id}.docx'
        }

    @staticmethod
    def _process_export_plano_acao_rich(task):
        """Processa exportação de plano de ação rico."""
        from apps.actions.models import PlanoAcao

        payload = task.payload
        plano_id = payload['plano_id']

        plano_acao = PlanoAcao.objects.get(id=plano_id)
        doc = ExportService.export_plano_acao_rich_word(plano_acao)

        buffer = BytesIO()
        doc.save(buffer)
        file_size = buffer.tell()
        buffer.close()

        return {
            'success': True,
            'file_size': file_size,
            'filename': f'plano_acao_rich_{plano_id}.docx'
        }

    @staticmethod
    def _process_export_checklist_nr1(task):
        """Processa exportação de checklist NR-1."""
        payload = task.payload
        campaign_id = payload['campaign_id']
        itens_por_etapa = payload['itens_por_etapa']
        progresso_geral = payload['progresso_geral']
        total_itens = payload['total_itens']
        total_concluidos = payload['total_concluidos']

        campaign = Campaign.objects.get(id=campaign_id)

        pdf_content = ExportService.export_checklist_nr1_pdf(
            campaign,
            itens_por_etapa,
            progresso_geral,
            total_itens,
            total_concluidos
        )

        # TODO: Salvar PDF em storage permanente

        return {
            'success': True,
            'file_size': len(pdf_content),
            'filename': f'checklist_nr1_{campaign_id}.pdf'
        }

    @staticmethod
    def _process_export_campaign_comparison(task):
        """Processa exportação de comparação de campanhas."""
        payload = task.payload
        campaign1_id = payload['campaign1_id']
        campaign2_id = payload['campaign2_id']
        summary = payload['summary']
        dimensions = payload['dimensions']
        sectors = payload['sectors']
        ai_analysis = payload.get('ai_analysis', '')

        campaign1 = Campaign.objects.get(id=campaign1_id)
        campaign2 = Campaign.objects.get(id=campaign2_id)

        doc = ExportService.export_campaign_comparison_word(
            campaign1,
            campaign2,
            summary,
            dimensions,
            sectors,
            ai_analysis
        )

        buffer = BytesIO()
        doc.save(buffer)
        file_size = buffer.tell()
        buffer.close()

        return {
            'success': True,
            'file_size': file_size,
            'filename': f'comparacao_campanhas_{campaign1_id}_{campaign2_id}.docx'
        }

    @staticmethod
    def _process_export_risk_matrix_excel(task):
        """Processa exportação de matriz de risco."""
        payload = task.payload
        campaign_id = payload['campaign_id']

        # TODO: Implementar usando PsychosocialRiskExportService
        # quando disponível

        return {
            'success': True,
            'filename': f'matriz_risco_{campaign_id}.xlsx'
        }


class TaskQueueWorker:
    """Worker que processa tarefas pendentes da fila."""

    @staticmethod
    def process_pending_tasks(limit=10):
        """
        Processa até 'limit' tarefas pendentes da fila.
        Retorna número de tarefas processadas com sucesso.
        """
        pending_tasks = TaskQueue.objects.filter(
            status='pending'
        ).order_by('created_at')[:limit]

        processed = 0
        for task in pending_tasks:
            # Verificar se já atingiu número máximo de tentativas
            if task.attempts >= task.max_attempts:
                task.status = 'failed'
                task.error_message = 'Número máximo de tentativas excedido'
                task.save()
                logger.warning(f"Tarefa {task.id} excedeu máximo de tentativas")
                continue

            # Processar tarefa
            success = TaskProcessor.process_task(task)
            if success:
                processed += 1

        return processed

    @staticmethod
    def retry_failed_tasks(limit=5):
        """
        Tenta reprocessar tarefas que falharam mas ainda têm tentativas disponíveis.
        """
        failed_tasks = TaskQueue.objects.filter(
            status='failed'
        ).exclude(
            attempts__gte=F('max_attempts')
        ).order_by('-created_at')[:limit]

        retried = 0
        for task in failed_tasks:
            task.status = 'pending'
            task.error_message = ''
            task.save()
            retried += 1
            logger.info(f"Tarefa {task.id} marcada para retry (tentativa {task.attempts + 1})")

        return retried
