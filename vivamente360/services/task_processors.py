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
from services.task_file_storage import TaskFileStorage
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
            elif task.task_type == 'export_pgr_document':
                result = TaskProcessor._process_export_pgr_document(task)
            else:
                logger.warning(f"Tipo de tarefa desconhecido: {task.task_type}")
                task.status = 'failed'
                task.error_message = f"Tipo de tarefa não suportado: {task.task_type}"
                task.save()
                return False

            # Marcar como concluída
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.progress = 100
            task.progress_message = 'Concluído'
            task.payload['result'] = result
            task.save()

            # Criar notificação de sucesso
            TaskProcessor._create_completion_notification(task, result)

            logger.info(f"Tarefa {task.id} ({task.task_type}) processada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao processar tarefa {task.id} ({task.task_type}): {str(e)}")
            task.status = 'failed'
            task.error_message = str(e)
            task.progress_message = 'Erro no processamento'
            task.save()

            # Criar notificação de falha
            TaskProcessor._create_failure_notification(task, str(e))

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

        task.progress = 25
        task.progress_message = 'Gerando documento...'
        task.save(update_fields=['progress', 'progress_message'])

        campaign = Campaign.objects.get(id=campaign_id)
        planos = PlanoAcao.objects.filter(id__in=plano_ids)

        doc = ExportService.export_plano_acao_word(campaign, planos)

        task.progress = 50
        task.progress_message = 'Salvando arquivo...'
        task.save(update_fields=['progress', 'progress_message'])

        # Salvar documento em storage permanente
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f'plano_acao_{campaign_id}.docx'
        file_type = TaskFileStorage.get_file_type_from_task_type(task.task_type)

        task.progress = 75
        task.progress_message = 'Finalizando...'
        task.save(update_fields=['progress', 'progress_message'])

        file_info = TaskFileStorage.save_task_file(buffer, filename, task.id, file_type)

        # Atualizar task com informações do arquivo
        task.file_path = file_info['file_path']
        task.file_name = file_info['file_name']
        task.file_size = file_info['file_size']
        task.save(update_fields=['file_path', 'file_name', 'file_size'])

        return {
            'success': True,
            'file_size': file_info['file_size'],
            'filename': file_info['file_name'],
            'file_path': file_info['file_path']
        }

    @staticmethod
    def _process_export_plano_acao_rich(task):
        """Processa exportação de plano de ação rico."""
        from apps.actions.models import PlanoAcao

        payload = task.payload
        plano_id = payload['plano_id']

        task.progress = 30
        task.progress_message = 'Gerando plano de ação detalhado...'
        task.save(update_fields=['progress', 'progress_message'])

        plano_acao = PlanoAcao.objects.get(id=plano_id)
        doc = ExportService.export_plano_acao_rich_word(plano_acao)

        task.progress = 70
        task.progress_message = 'Salvando arquivo...'
        task.save(update_fields=['progress', 'progress_message'])

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f'plano_acao_detalhado_{plano_id}.docx'
        file_type = TaskFileStorage.get_file_type_from_task_type(task.task_type)

        file_info = TaskFileStorage.save_task_file(buffer, filename, task.id, file_type)

        task.file_path = file_info['file_path']
        task.file_name = file_info['file_name']
        task.file_size = file_info['file_size']
        task.save(update_fields=['file_path', 'file_name', 'file_size'])

        return {
            'success': True,
            'file_size': file_info['file_size'],
            'filename': file_info['file_name'],
            'file_path': file_info['file_path']
        }

    @staticmethod
    def _process_export_checklist_nr1(task):
        """Processa exportação de checklist NR-1."""
        from apps.actions.models import ChecklistNR1Etapa

        payload = task.payload
        campaign_id = payload['campaign_id']
        progresso_geral = payload['progresso_geral']
        total_itens = payload['total_itens']
        total_concluidos = payload['total_concluidos']

        task.progress = 30
        task.progress_message = 'Gerando checklist NR-1...'
        task.save(update_fields=['progress', 'progress_message'])

        campaign = Campaign.objects.get(id=campaign_id)

        # Reconstruir itens_por_etapa com objetos do modelo
        itens_por_etapa_payload = payload['itens_por_etapa']
        itens_por_etapa = {}

        for etapa_num_str, etapa_data in itens_por_etapa_payload.items():
            etapa_num = int(etapa_num_str)
            # Buscar os itens reais do banco de dados
            item_ids = [item['id'] for item in etapa_data['itens']]
            itens_obj = ChecklistNR1Etapa.objects.filter(id__in=item_ids).order_by('item_ordem')

            itens_por_etapa[etapa_num] = {
                'nome': etapa_data['nome'],
                'itens': itens_obj,
                'total': etapa_data['total'],
                'concluidos': etapa_data['concluidos'],
                'progresso': etapa_data['progresso']
            }

        pdf_content = ExportService.export_checklist_nr1_pdf(
            campaign,
            itens_por_etapa,
            progresso_geral,
            total_itens,
            total_concluidos
        )

        task.progress = 70
        task.progress_message = 'Salvando PDF...'
        task.save(update_fields=['progress', 'progress_message'])

        filename = f'checklist_nr1_{campaign_id}.pdf'
        file_type = TaskFileStorage.get_file_type_from_task_type(task.task_type)

        file_info = TaskFileStorage.save_task_file(pdf_content, filename, task.id, file_type)

        task.file_path = file_info['file_path']
        task.file_name = file_info['file_name']
        task.file_size = file_info['file_size']
        task.save(update_fields=['file_path', 'file_name', 'file_size'])

        return {
            'success': True,
            'file_size': file_info['file_size'],
            'filename': file_info['file_name'],
            'file_path': file_info['file_path']
        }

    @staticmethod
    def _process_export_campaign_comparison(task):
        """Processa exportação de comparação de campanhas."""
        from app_selectors.comparison_selectors import ComparisonSelectors

        payload = task.payload
        campaign1_id = payload['campaign1_id']
        campaign2_id = payload['campaign2_id']

        task.progress = 20
        task.progress_message = 'Buscando dados das campanhas...'
        task.save(update_fields=['progress', 'progress_message'])

        campaign1 = Campaign.objects.get(id=campaign1_id)
        campaign2 = Campaign.objects.get(id=campaign2_id)

        task.progress = 40
        task.progress_message = 'Comparando campanhas...'
        task.save(update_fields=['progress', 'progress_message'])

        # Buscar dados de comparação
        summary = ComparisonSelectors.get_evolution_summary(campaign1, campaign2)
        dimensions = ComparisonSelectors.get_evolution_by_dimension(campaign1, campaign2)
        sectors = ComparisonSelectors.get_top_sectors_evolution(campaign1, campaign2)

        # Gerar análise de IA
        evolution_data = {
            'summary': summary,
            'dimensions': dimensions,
            'sectors': sectors,
        }
        ai_analysis = ComparisonSelectors.generate_ai_analysis(campaign1, campaign2, evolution_data)

        task.progress = 60
        task.progress_message = 'Gerando documento...'
        task.save(update_fields=['progress', 'progress_message'])

        doc = ExportService.export_campaign_comparison_word(
            campaign1,
            campaign2,
            summary,
            dimensions,
            sectors,
            ai_analysis
        )

        task.progress = 80
        task.progress_message = 'Salvando relatório...'
        task.save(update_fields=['progress', 'progress_message'])

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f'Relatorio_Evolucao_{campaign1.empresa.nome.replace(" ", "_")}.docx'
        file_type = TaskFileStorage.get_file_type_from_task_type(task.task_type)

        file_info = TaskFileStorage.save_task_file(buffer, filename, task.id, file_type)

        task.file_path = file_info['file_path']
        task.file_name = file_info['file_name']
        task.file_size = file_info['file_size']
        task.save(update_fields=['file_path', 'file_name', 'file_size'])

        return {
            'success': True,
            'file_size': file_info['file_size'],
            'filename': file_info['file_name'],
            'file_path': file_info['file_path']
        }

    @staticmethod
    def _process_export_risk_matrix_excel(task):
        """Processa exportação de matriz de risco em Excel."""
        from services.risk_assessment_service import RiskAssessmentService
        from services.psychosocial_risk_export_service import PsychosocialRiskExportService

        payload = task.payload
        campaign_id = payload['campaign_id']

        task.progress = 20
        task.progress_message = 'Buscando dados da campanha...'
        task.save(update_fields=['progress', 'progress_message'])

        campaign = Campaign.objects.get(id=campaign_id)

        task.progress = 40
        task.progress_message = 'Avaliando riscos psicossociais...'
        task.save(update_fields=['progress', 'progress_message'])

        # Gerar avaliação completa com processamento de IA
        avaliacao = RiskAssessmentService.avaliar_campanha_completa(
            campaign,
            processar_ia=True
        )

        task.progress = 70
        task.progress_message = 'Gerando planilha Excel...'
        task.save(update_fields=['progress', 'progress_message'])

        # Gerar Excel
        excel_file = PsychosocialRiskExportService.export_to_excel(avaliacao)

        task.progress = 85
        task.progress_message = 'Salvando arquivo...'
        task.save(update_fields=['progress', 'progress_message'])

        # Salvar em buffer
        buffer = BytesIO()
        excel_file.save(buffer)
        buffer.seek(0)

        filename = f"Matriz_Risco_Psicossocial_{campaign.empresa.nome.replace(' ', '_')}_{campaign.nome.replace(' ', '_')}.xlsx"
        file_type = TaskFileStorage.get_file_type_from_task_type(task.task_type)

        file_info = TaskFileStorage.save_task_file(buffer, filename, task.id, file_type)

        task.file_path = file_info['file_path']
        task.file_name = file_info['file_name']
        task.file_size = file_info['file_size']
        task.save(update_fields=['file_path', 'file_name', 'file_size'])

        return {
            'success': True,
            'file_size': file_info['file_size'],
            'filename': file_info['file_name'],
            'file_path': file_info['file_path']
        }

    @staticmethod
    def _process_export_pgr_document(task):
        """Processa exportação de documento PGR (Programa de Gerenciamento de Riscos)."""
        from services.risk_assessment_service import RiskAssessmentService
        from services.psychosocial_risk_export_service import PsychosocialRiskExportService

        payload = task.payload
        campaign_id = payload['campaign_id']

        task.progress = 20
        task.progress_message = 'Buscando dados da campanha...'
        task.save(update_fields=['progress', 'progress_message'])

        campaign = Campaign.objects.get(id=campaign_id)

        task.progress = 40
        task.progress_message = 'Avaliando riscos psicossociais...'
        task.save(update_fields=['progress', 'progress_message'])

        # Gerar avaliação completa com processamento de IA
        avaliacao = RiskAssessmentService.avaliar_campanha_completa(
            campaign,
            processar_ia=True
        )

        task.progress = 70
        task.progress_message = 'Gerando documento PGR...'
        task.save(update_fields=['progress', 'progress_message'])

        # Gerar documento PGR
        doc_bio = PsychosocialRiskExportService.export_pgr_document(avaliacao)

        task.progress = 85
        task.progress_message = 'Salvando arquivo...'
        task.save(update_fields=['progress', 'progress_message'])

        filename = f"PGR_Riscos_Psicossociais_{campaign.empresa.nome.replace(' ', '_')}.txt"
        file_type = TaskFileStorage.get_file_type_from_task_type(task.task_type)

        file_info = TaskFileStorage.save_task_file(doc_bio, filename, task.id, file_type)

        task.file_path = file_info['file_path']
        task.file_name = file_info['file_name']
        task.file_size = file_info['file_size']
        task.save(update_fields=['file_path', 'file_name', 'file_size'])

        return {
            'success': True,
            'file_size': file_info['file_size'],
            'filename': file_info['file_name'],
            'file_path': file_info['file_path']
        }

    @staticmethod
    def _create_completion_notification(task, result):
        """Cria notificação de task completada."""
        from apps.core.models import UserNotification

        if not task.user:
            return

        # Mapear tipos de task para mensagens amigáveis
        task_names = {
            'send_email': 'E-mail enviado',
            'generate_sector_analysis': 'Análise de setor gerada',
            'import_csv': 'Importação de dados concluída',
            'export_plano_acao': 'Plano de ação exportado',
            'export_plano_acao_rich': 'Plano de ação detalhado exportado',
            'export_checklist_nr1': 'Checklist NR-1 exportado',
            'export_campaign_comparison': 'Comparação de campanhas exportada',
            'export_risk_matrix_excel': 'Matriz de risco exportada',
            'export_pgr_document': 'Documento PGR exportado',
        }

        title = task_names.get(task.task_type, 'Tarefa concluída')

        # Determinar tipo de notificação e mensagem
        if task.is_file_task:
            notification_type = 'file_ready'
            message = f'{title}. Seu arquivo está pronto para download.'
            link_url = f'/tasks/download/{task.id}/'
            link_text = 'Baixar arquivo'
        else:
            notification_type = 'task_completed'
            message = f'{title} com sucesso.'
            link_url = ''
            link_text = ''

        try:
            # Verificar se já existe notificação para esta task
            existing = UserNotification.objects.filter(
                user=task.user,
                task=task,
                notification_type=notification_type
            ).exists()

            if existing:
                logger.info(f"Notificação já existe para task {task.id}, pulando criação")
                return

            UserNotification.objects.create(
                user=task.user,
                empresa=task.empresa,
                notification_type=notification_type,
                title=title,
                message=message,
                task=task,
                link_url=link_url,
                link_text=link_text
            )
            logger.info(f"Notificação de sucesso criada para task {task.id}")
        except Exception as e:
            logger.error(f"Erro ao criar notificação de sucesso: {str(e)}")

    @staticmethod
    def _create_failure_notification(task, error_message):
        """Cria notificação de task falhada."""
        from apps.core.models import UserNotification

        if not task.user:
            return

        task_names = {
            'send_email': 'Erro ao enviar e-mail',
            'generate_sector_analysis': 'Erro na análise de setor',
            'import_csv': 'Erro na importação de dados',
            'export_plano_acao': 'Erro ao exportar plano de ação',
            'export_plano_acao_rich': 'Erro ao exportar plano de ação detalhado',
            'export_checklist_nr1': 'Erro ao exportar checklist NR-1',
            'export_campaign_comparison': 'Erro ao exportar comparação',
            'export_risk_matrix_excel': 'Erro ao exportar matriz de risco',
            'export_pgr_document': 'Erro ao exportar documento PGR',
        }

        title = task_names.get(task.task_type, 'Erro na tarefa')

        # Truncar mensagem de erro se muito longa
        error_preview = error_message[:200] + '...' if len(error_message) > 200 else error_message

        try:
            # Verificar se já existe notificação para esta task
            existing = UserNotification.objects.filter(
                user=task.user,
                task=task,
                notification_type='task_failed'
            ).exists()

            if existing:
                logger.info(f"Notificação de falha já existe para task {task.id}, pulando criação")
                return

            UserNotification.objects.create(
                user=task.user,
                empresa=task.empresa,
                notification_type='task_failed',
                title=title,
                message=f'Houve um erro ao processar sua solicitação: {error_preview}',
                task=task
            )
            logger.info(f"Notificação de falha criada para task {task.id}")
        except Exception as e:
            logger.error(f"Erro ao criar notificação de falha: {str(e)}")


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
