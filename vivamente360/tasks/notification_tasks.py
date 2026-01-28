"""
Tasks Celery para processamento de notificações do sistema Vivamente360.

Este módulo contém tasks assíncronas para:
- Processar fila de notificações pendentes
- Verificar e enviar alertas programados
- Monitorar métricas de campanhas e planos de ação
"""

from celery import shared_task
from datetime import date, timedelta
from django.utils import timezone
from vivamente360.apps.core.models import TaskQueue
from vivamente360.services.notification_service import NotificationService
from vivamente360.services.email_service import get_email_service
import logging

logger = logging.getLogger(__name__)


@shared_task(name='process_notification_queue')
def process_notification_queue(batch_size=10, max_attempts=3):
    """
    Processa fila de notificações pendentes.

    Esta task busca notificações na TaskQueue com status 'pending' e
    processa o envio usando o EmailService configurado.

    Args:
        batch_size (int): Número máximo de notificações a processar por execução
        max_attempts (int): Número máximo de tentativas de envio

    Returns:
        dict: Estatísticas do processamento
            - processed: Total processado
            - success: Emails enviados com sucesso
            - failed: Emails que falharam
            - skipped: Emails ignorados (excederam max_attempts)

    Exemplo de uso:
        # Executar manualmente
        from vivamente360.tasks.notification_tasks import process_notification_queue
        result = process_notification_queue.delay(batch_size=20)

        # Agendamento periódico (configurar em celery beat)
        # CELERY_BEAT_SCHEDULE = {
        #     'process-notifications-every-5-minutes': {
        #         'task': 'process_notification_queue',
        #         'schedule': timedelta(minutes=5),
        #     },
        # }
    """
    stats = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0,
    }

    try:
        # Buscar notificações pendentes
        pending_tasks = TaskQueue.objects.filter(
            task_type='send_notification_email',
            status='pending'
        ).order_by('created_at')[:batch_size]

        email_service = get_email_service()

        for task in pending_tasks:
            stats['processed'] += 1

            try:
                # Verificar número de tentativas
                if task.attempts >= max_attempts:
                    task.status = 'failed'
                    task.error_message = f"Excedeu número máximo de tentativas ({max_attempts})"
                    task.save()
                    stats['skipped'] += 1
                    logger.warning(f"Task #{task.id} excedeu max_attempts")
                    continue

                # Atualizar status e tentativas
                task.status = 'processing'
                task.attempts += 1
                task.save()

                # Extrair dados do payload
                payload = task.payload
                to_email = payload.get('to')
                subject = payload.get('subject')
                html_body = payload.get('html_body')

                # Validar dados
                if not all([to_email, subject, html_body]):
                    raise ValueError("Payload incompleto: faltam campos obrigatórios")

                # Enviar email
                success = email_service.send(
                    to=to_email,
                    subject=subject,
                    html_body=html_body
                )

                if success:
                    task.status = 'completed'
                    task.completed_at = timezone.now()
                    task.save()
                    stats['success'] += 1
                    logger.info(f"Task #{task.id} processada com sucesso")
                else:
                    raise Exception("EmailService retornou False")

            except Exception as e:
                task.status = 'failed' if task.attempts >= max_attempts else 'pending'
                task.error_message = str(e)
                task.save()
                stats['failed'] += 1
                logger.error(f"Erro ao processar Task #{task.id}: {str(e)}", exc_info=True)

        logger.info(f"Processamento de notificações concluído: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Erro crítico no processamento de notificações: {str(e)}", exc_info=True)
        raise


@shared_task(name='check_campaign_adhesion')
def check_campaign_adhesion():
    """
    Verifica adesão de campanhas ativas e envia alertas se necessário.

    Verifica todas as campanhas com status 'active' e envia alerta
    quando a taxa de adesão está abaixo de 50%.

    Returns:
        dict: Estatísticas da verificação
            - campaigns_checked: Total de campanhas verificadas
            - alerts_sent: Total de alertas enviados

    Nota:
        Esta task deve ser executada periodicamente (ex: diariamente).
    """
    stats = {
        'campaigns_checked': 0,
        'alerts_sent': 0,
    }

    try:
        from vivamente360.apps.surveys.models import Campaign

        # Buscar campanhas ativas
        active_campaigns = Campaign.objects.filter(status='active')

        for campaign in active_campaigns:
            stats['campaigns_checked'] += 1

            try:
                # Enviar alerta se adesão baixa
                tasks = NotificationService.alerta_adesao_baixa(campaign)

                if tasks:
                    stats['alerts_sent'] += len(tasks)
                    logger.info(
                        f"Alerta de adesão baixa enviado para campanha {campaign.id} "
                        f"({len(tasks)} destinatários)"
                    )

            except Exception as e:
                logger.error(
                    f"Erro ao verificar adesão da campanha {campaign.id}: {str(e)}",
                    exc_info=True
                )

        logger.info(f"Verificação de adesão concluída: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Erro crítico na verificação de adesão: {str(e)}", exc_info=True)
        raise


@shared_task(name='check_action_plan_deadlines')
def check_action_plan_deadlines(dias_antecedencia=7):
    """
    Verifica prazos de planos de ação e envia alertas para ações vencendo.

    Args:
        dias_antecedencia (int): Dias de antecedência para enviar alerta

    Returns:
        dict: Estatísticas da verificação
            - plans_checked: Total de planos verificados
            - alerts_sent: Total de alertas enviados

    Nota:
        Esta task deve ser executada diariamente.
    """
    stats = {
        'plans_checked': 0,
        'alerts_sent': 0,
    }

    try:
        from vivamente360.apps.actions.models import PlanoAcao

        # Data limite para alertas
        data_limite = date.today() + timedelta(days=dias_antecedencia)

        # Buscar planos de ação com prazo próximo
        planos = PlanoAcao.objects.filter(
            status__in=['pendente', 'andamento'],
            prazo__lte=data_limite,
            prazo__gte=date.today()
        )

        for plano in planos:
            stats['plans_checked'] += 1

            try:
                # Enviar alerta
                task = NotificationService.alerta_prazo_vencendo(
                    plano,
                    dias_antecedencia=dias_antecedencia
                )

                if task:
                    stats['alerts_sent'] += 1
                    logger.info(f"Alerta de prazo enviado para PlanoAcao {plano.id}")

            except Exception as e:
                logger.error(
                    f"Erro ao verificar prazo do PlanoAcao {plano.id}: {str(e)}",
                    exc_info=True
                )

        logger.info(f"Verificação de prazos concluída: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Erro crítico na verificação de prazos: {str(e)}", exc_info=True)
        raise


@shared_task(name='check_critical_risks')
def check_critical_risks():
    """
    Verifica respostas recentes para identificar riscos críticos.

    Processa respostas das últimas 24 horas e envia alertas quando
    detecta colaboradores em situação de risco crítico.

    Returns:
        dict: Estatísticas da verificação
            - responses_checked: Total de respostas verificadas
            - alerts_sent: Total de alertas enviados

    Nota:
        Esta task deve ser executada periodicamente (ex: a cada 6 horas).
    """
    stats = {
        'responses_checked': 0,
        'alerts_sent': 0,
    }

    try:
        from vivamente360.apps.responses.models import SurveyResponse

        # Buscar respostas das últimas 24 horas
        cutoff_time = timezone.now() - timedelta(hours=24)
        recent_responses = SurveyResponse.objects.filter(
            created_at__gte=cutoff_time
        )

        for response in recent_responses:
            stats['responses_checked'] += 1

            try:
                # Verificar risco crítico
                tasks = NotificationService.alerta_risco_critico(response)

                if tasks:
                    stats['alerts_sent'] += len(tasks)
                    logger.info(
                        f"Alerta de risco crítico enviado para SurveyResponse {response.id} "
                        f"({len(tasks)} destinatários)"
                    )

            except Exception as e:
                logger.error(
                    f"Erro ao verificar risco de SurveyResponse {response.id}: {str(e)}",
                    exc_info=True
                )

        logger.info(f"Verificação de riscos críticos concluída: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Erro crítico na verificação de riscos: {str(e)}", exc_info=True)
        raise


@shared_task(name='send_bulk_notifications')
def send_bulk_notifications(notification_ids):
    """
    Envia notificações em lote usando bulk email.

    Args:
        notification_ids (list): Lista de IDs de TaskQueue para processar

    Returns:
        dict: Resultado do envio em lote

    Nota:
        Útil para envio de notificações em massa (ex: resultados de campanha).
    """
    try:
        tasks = TaskQueue.objects.filter(
            id__in=notification_ids,
            task_type='send_notification_email',
            status='pending'
        )

        if not tasks.exists():
            logger.warning("Nenhuma notificação encontrada para envio em lote")
            return {'sent': 0, 'failed': 0}

        # Preparar lista de emails
        emails = []
        for task in tasks:
            payload = task.payload
            emails.append({
                'to': payload.get('to'),
                'subject': payload.get('subject'),
                'html_body': payload.get('html_body'),
            })

            # Marcar como processando
            task.status = 'processing'
            task.attempts += 1
            task.save()

        # Enviar em lote
        email_service = get_email_service()
        result = email_service.send_bulk(emails)

        # Atualizar status das tasks
        success_count = result.get('sent', 0)
        failed_count = result.get('failed', 0)

        # Simplificação: marcar todas como completed se maioria teve sucesso
        if success_count > failed_count:
            tasks.update(status='completed', completed_at=timezone.now())
        else:
            tasks.update(status='failed', error_message='Falha no envio em lote')

        logger.info(f"Envio em lote concluído: {result}")
        return result

    except Exception as e:
        logger.error(f"Erro no envio em lote: {str(e)}", exc_info=True)
        tasks.update(status='failed', error_message=str(e))
        raise
