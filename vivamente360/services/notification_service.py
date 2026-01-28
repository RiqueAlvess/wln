"""
Serviço de notificações por email para o sistema Vivamente360.

Este módulo gerencia o envio de notificações automáticas relacionadas a:
- Resultados individuais de questionários
- Alertas de adesão baixa em campanhas
- Alertas de risco crítico
- Alertas de prazos vencendo em planos de ação
"""

from datetime import date, timedelta
from django.conf import settings
from django.template.loader import render_to_string
from vivamente360.services.email_service import get_email_service
from vivamente360.apps.core.models import TaskQueue
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Serviço centralizado para gerenciamento de notificações por email.

    Utiliza o EmailService existente e TaskQueue para processamento assíncrono.
    """

    @staticmethod
    def _enfileirar_email(to_email, subject, html_body, task_metadata=None):
        """
        Adiciona um email à fila de processamento.

        Args:
            to_email (str): Email do destinatário
            subject (str): Assunto do email
            html_body (str): Corpo do email em HTML
            task_metadata (dict): Metadados adicionais para rastreamento

        Returns:
            TaskQueue: Objeto da tarefa criada
        """
        payload = {
            'to': to_email,
            'subject': subject,
            'html_body': html_body,
            'from_email': settings.DEFAULT_FROM_EMAIL,
        }

        if task_metadata:
            payload['metadata'] = task_metadata

        task = TaskQueue.objects.create(
            task_type='send_notification_email',
            payload=payload,
            status='pending'
        )

        logger.info(f"Email enfileirado: {subject} para {to_email} (Task #{task.id})")
        return task

    @staticmethod
    def enviar_resultado_individual(survey_response):
        """
        Envia email com resultado individual após conclusão do questionário.

        Args:
            survey_response: Objeto SurveyResponse com as respostas do questionário

        Returns:
            TaskQueue: Tarefa de envio criada ou None se não for possível enviar

        Nota:
            Requer que o survey_response tenha email do respondente disponível.
            Por questões de LGPD, o email pode estar na SurveyInvitation relacionada.
        """
        try:
            # Buscar convite relacionado para obter email do respondente
            from vivamente360.apps.invitations.models import SurveyInvitation

            invitation = SurveyInvitation.objects.filter(
                campaign=survey_response.campaign,
                # Aqui seria necessário um identificador único do respondente
                # Por enquanto, estrutura básica
            ).first()

            if not invitation:
                logger.warning(
                    f"Não foi possível enviar resultado individual: "
                    f"convite não encontrado para SurveyResponse #{survey_response.id}"
                )
                return None

            # Calcular scores por dimensão
            from vivamente360.app_selectors.analytics_selectors import AnalyticsSelectors
            scores = AnalyticsSelectors.calcular_scores_individuais(survey_response)

            # Renderizar template de email
            html_body = render_to_string('emails/resultado_individual.html', {
                'campaign': survey_response.campaign,
                'scores': scores,
                'empresa': survey_response.campaign.empresa,
                'data_resposta': survey_response.created_at,
            })

            subject = f"Seu resultado - {survey_response.campaign.nome}"

            # Enviar email de forma assíncrona
            return NotificationService._enfileirar_email(
                to_email=invitation.email_destinatario,
                subject=subject,
                html_body=html_body,
                task_metadata={
                    'tipo': 'resultado_individual',
                    'survey_response_id': survey_response.id,
                    'campaign_id': survey_response.campaign.id,
                }
            )

        except Exception as e:
            logger.error(f"Erro ao enviar resultado individual: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def alerta_adesao_baixa(campaign):
        """
        Alerta gestores quando adesão < 50%.

        Args:
            campaign: Objeto Campaign a ser verificado

        Returns:
            list[TaskQueue]: Lista de tarefas de envio criadas

        Nota:
            Envia alerta para o criador da campanha e gestores da empresa.
        """
        try:
            from vivamente360.apps.invitations.models import SurveyInvitation
            from vivamente360.apps.responses.models import SurveyResponse

            # Calcular taxa de adesão
            total_convidados = SurveyInvitation.objects.filter(
                campaign=campaign,
                status='sent'
            ).count()

            total_respostas = SurveyResponse.objects.filter(
                campaign=campaign
            ).count()

            if total_convidados == 0:
                logger.warning(f"Campanha {campaign.id} sem convites enviados")
                return []

            taxa_adesao = (total_respostas / total_convidados) * 100

            # Verificar se adesão está abaixo de 50%
            if taxa_adesao >= 50:
                logger.info(f"Campanha {campaign.id} com adesão adequada: {taxa_adesao:.1f}%")
                return []

            # Renderizar template de alerta
            html_body = render_to_string('emails/alerta_adesao.html', {
                'campaign': campaign,
                'taxa_adesao': taxa_adesao,
                'total_convidados': total_convidados,
                'total_respostas': total_respostas,
                'empresa': campaign.empresa,
            })

            subject = f"⚠️ Alerta: Baixa adesão na campanha {campaign.nome}"

            # Enviar para criador da campanha
            tasks = []
            if campaign.created_by and campaign.created_by.email:
                task = NotificationService._enfileirar_email(
                    to_email=campaign.created_by.email,
                    subject=subject,
                    html_body=html_body,
                    task_metadata={
                        'tipo': 'alerta_adesao_baixa',
                        'campaign_id': campaign.id,
                        'taxa_adesao': taxa_adesao,
                    }
                )
                tasks.append(task)

            # TODO: Enviar para outros gestores da empresa
            # Implementar quando houver model de gestores/permissões

            return tasks

        except Exception as e:
            logger.error(f"Erro ao enviar alerta de adesão baixa: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def alerta_risco_critico(survey_response):
        """
        Alerta quando colaborador classificado como risco crítico.

        Args:
            survey_response: Objeto SurveyResponse a ser avaliado

        Returns:
            list[TaskQueue]: Lista de tarefas de envio criadas

        Nota:
            Considera risco crítico quando:
            - Score médio < 2.0 em qualquer dimensão negativa
            - Score médio < 2.5 em múltiplas dimensões
        """
        try:
            from vivamente360.app_selectors.analytics_selectors import AnalyticsSelectors

            # Calcular scores individuais
            scores = AnalyticsSelectors.calcular_scores_individuais(survey_response)

            # Verificar critérios de risco crítico
            dimensoes_criticas = []
            for dimensao, score in scores.items():
                if score < 2.0:
                    dimensoes_criticas.append({
                        'dimensao': dimensao,
                        'score': score,
                        'nivel': 'crítico'
                    })
                elif score < 2.5:
                    dimensoes_criticas.append({
                        'dimensao': dimensao,
                        'score': score,
                        'nivel': 'atenção'
                    })

            # Verificar se há risco crítico
            tem_risco_critico = any(
                d['nivel'] == 'crítico' for d in dimensoes_criticas
            ) or len(dimensoes_criticas) >= 3

            if not tem_risco_critico:
                return []

            # Renderizar template de alerta
            html_body = render_to_string('emails/alerta_risco_critico.html', {
                'campaign': survey_response.campaign,
                'survey_response': survey_response,
                'dimensoes_criticas': dimensoes_criticas,
                'empresa': survey_response.campaign.empresa,
                'unidade': survey_response.unidade,
                'setor': survey_response.setor,
                'cargo': survey_response.cargo,
            })

            subject = f"🚨 Alerta: Risco crítico detectado - {survey_response.campaign.nome}"

            # Enviar para criador da campanha
            tasks = []
            if survey_response.campaign.created_by and survey_response.campaign.created_by.email:
                task = NotificationService._enfileirar_email(
                    to_email=survey_response.campaign.created_by.email,
                    subject=subject,
                    html_body=html_body,
                    task_metadata={
                        'tipo': 'alerta_risco_critico',
                        'survey_response_id': survey_response.id,
                        'campaign_id': survey_response.campaign.id,
                        'dimensoes_criticas': len(dimensoes_criticas),
                    }
                )
                tasks.append(task)

            # TODO: Enviar para RH e gestores responsáveis

            return tasks

        except Exception as e:
            logger.error(f"Erro ao enviar alerta de risco crítico: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def alerta_prazo_vencendo(plano_acao, dias_antecedencia=7):
        """
        Alerta quando prazo de ação está vencendo.

        Args:
            plano_acao: Objeto PlanoAcao a ser verificado
            dias_antecedencia (int): Dias antes do prazo para enviar alerta

        Returns:
            TaskQueue: Tarefa de envio criada ou None

        Nota:
            Envia alerta apenas para planos pendentes ou em andamento.
        """
        try:
            # Verificar se plano está em status que requer alerta
            if plano_acao.status not in ['pendente', 'andamento']:
                return None

            # Calcular dias restantes
            dias_restantes = (plano_acao.prazo - date.today()).days

            # Verificar se está dentro do período de alerta
            if dias_restantes > dias_antecedencia or dias_restantes < 0:
                return None

            # Determinar urgência
            if dias_restantes == 0:
                urgencia = 'hoje'
                emoji = '🚨'
            elif dias_restantes <= 3:
                urgencia = 'urgente'
                emoji = '⚠️'
            else:
                urgencia = 'normal'
                emoji = '📅'

            # Renderizar template de alerta
            html_body = render_to_string('emails/alerta_prazo.html', {
                'plano_acao': plano_acao,
                'dias_restantes': dias_restantes,
                'urgencia': urgencia,
                'empresa': plano_acao.empresa,
                'campaign': plano_acao.campaign,
            })

            subject = f"{emoji} Alerta: Plano de ação vence em {dias_restantes} dia(s)"

            # Enviar para responsável (extrair email do campo responsavel se for email)
            # TODO: Implementar extração de email do responsável quando for um User

            # Por enquanto, enviar para criador da campanha
            if plano_acao.campaign.created_by and plano_acao.campaign.created_by.email:
                return NotificationService._enfileirar_email(
                    to_email=plano_acao.campaign.created_by.email,
                    subject=subject,
                    html_body=html_body,
                    task_metadata={
                        'tipo': 'alerta_prazo_vencendo',
                        'plano_acao_id': plano_acao.id,
                        'campaign_id': plano_acao.campaign.id,
                        'dias_restantes': dias_restantes,
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Erro ao enviar alerta de prazo vencendo: {str(e)}", exc_info=True)
            return None
