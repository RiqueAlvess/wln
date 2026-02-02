from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from cryptography.exceptions import InvalidTag
from apps.core.mixins import RHRequiredMixin
from apps.invitations.models import SurveyInvitation
from apps.surveys.models import Campaign
from apps.core.models import TaskQueue
from services.crypto_service import CryptoService
from services.import_service import ImportService
from services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


class ManageInvitationsView(RHRequiredMixin, ListView):
    model = SurveyInvitation
    template_name = 'invitations/manage.html'
    context_object_name = 'invitations'
    paginate_by = 50

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        queryset = SurveyInvitation.objects.filter(campaign_id=campaign_id).select_related(
            'unidade', 'setor', 'cargo'
        )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        context['campaign'] = get_object_or_404(Campaign, id=campaign_id)

        base_queryset = SurveyInvitation.objects.filter(campaign_id=campaign_id)

        context['total_count'] = base_queryset.count()
        context['pending_count'] = base_queryset.filter(status='pending').count()
        context['sent_count'] = base_queryset.filter(status='sent').count()
        context['used_count'] = base_queryset.filter(status='used').count()
        context['filter_status'] = self.request.GET.get('status', '')

        return context


class ImportCSVView(RHRequiredMixin, View):
    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        return render(request, 'invitations/import_csv.html', {'campaign': campaign})

    def post(self, request, campaign_id):
        from django.http import JsonResponse

        campaign = get_object_or_404(Campaign, id=campaign_id)
        csv_file = request.FILES.get('csv_file')

        # Verificar se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not csv_file:
            if is_ajax:
                return JsonResponse({'error': 'Nenhum arquivo foi enviado.'}, status=400)
            messages.error(request, 'Nenhum arquivo foi enviado.')
            return redirect('invitations:import', campaign_id=campaign_id)

        content = csv_file.read().decode('utf-8')
        valid, error, rows = ImportService.validate_csv(content)

        if not valid:
            if is_ajax:
                return JsonResponse({'error': error}, status=400)
            messages.error(request, error)
            return redirect('invitations:import', campaign_id=campaign_id)

        # Enfileirar tarefa de importação no banco de dados
        task = TaskQueue.objects.create(
            task_type='import_csv',
            payload={
                'campaign_id': campaign_id,
                'empresa_id': campaign.empresa.id,
                'rows': rows,
                'user_id': request.user.id
            }
        )

        AuditService.log(
            request.user,
            campaign.empresa,
            'import_csv',
            f'Importação de {len(rows)} registros enfileirada (Task #{task.id})',
            request
        )

        # Se for AJAX, retornar JSON
        if is_ajax:
            return JsonResponse({
                'task_id': task.id,
                'message': f'Importação de {len(rows)} registros iniciada. Você será notificado quando concluir.',
                'status_url': f'/api/tasks/{task.id}/',
                'redirect_url': f'/invitations/{campaign_id}/manage/'
            })

        # Caso contrário, comportamento legacy com messages
        messages.success(
            request,
            f'Importação de {len(rows)} registros enfileirada com sucesso. '
            f'Você será notificado quando concluir.'
        )
        return redirect('invitations:manage', campaign_id=campaign_id)


class DispatchEmailsView(RHRequiredMixin, View):
    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        invitations = SurveyInvitation.objects.filter(
            campaign=campaign, status='pending'
        ).select_related('campaign', 'empresa')

        crypto_service = CryptoService()
        count = 0
        failed_count = 0

        for invitation in invitations:
            try:
                email = crypto_service.decrypt(invitation.email_encrypted)
                magic_link = f"{request.scheme}://{request.get_host()}/survey/{invitation.hash_token}/"

                html_body = f"""
                <h2>Pesquisa de Clima Organizacional - {campaign.empresa.nome_app}</h2>
                <p>Você foi convidado(a) a participar da pesquisa {campaign.nome}.</p>
                <p><a href="{magic_link}">Clique aqui para responder</a></p>
                <p>Este link expira em 48 horas e só pode ser usado uma vez.</p>
                """

                TaskQueue.objects.create(
                    task_type='send_email',
                    payload={
                        'to': email,
                        'subject': f'Pesquisa {campaign.nome} - {campaign.empresa.nome}',
                        'html': html_body,
                        'invitation_id': invitation.id
                    }
                )
                count += 1

            except InvalidTag:
                failed_count += 1
                logger.error(
                    f"Erro de descriptografia para convite ID {invitation.id}. "
                    f"O email pode ter sido criptografado com uma chave diferente."
                )
                messages.warning(
                    request,
                    f"Convite ID {invitation.id}: Não foi possível descriptografar o email. "
                    f"O convite pode ter sido criado com uma chave de criptografia diferente."
                )

            except Exception as e:
                failed_count += 1
                logger.error(f"Erro ao processar convite ID {invitation.id}: {str(e)}")
                messages.warning(
                    request,
                    f"Convite ID {invitation.id}: Erro ao processar - {str(e)}"
                )

        if count > 0:
            messages.success(request, f'{count} e-mails enfileirados para envio.')
            AuditService.log(request.user, campaign.empresa, 'disparo_email',
                             f'Disparados {count} e-mails', request)

        if failed_count > 0:
            messages.error(
                request,
                f'{failed_count} convites falharam. Verifique os logs para mais detalhes.'
            )

        return redirect('invitations:manage', campaign_id=campaign_id)
