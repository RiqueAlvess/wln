from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.core.mixins import RHRequiredMixin
from apps.invitations.models import SurveyInvitation
from apps.surveys.models import Campaign
from apps.core.models import TaskQueue
from services.crypto_service import CryptoService
from services.import_service import ImportService
from services.audit_service import AuditService


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
        context['pending_count'] = SurveyInvitation.objects.filter(
            campaign_id=campaign_id, status='pending'
        ).count()
        return context


class ImportCSVView(RHRequiredMixin, View):
    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        return render(request, 'invitations/import_csv.html', {'campaign': campaign})

    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, 'Nenhum arquivo foi enviado.')
            return redirect('invitations:import', campaign_id=campaign_id)

        content = csv_file.read().decode('utf-8')
        valid, error, rows = ImportService.validate_csv(content)

        if not valid:
            messages.error(request, error)
            return redirect('invitations:import', campaign_id=campaign_id)

        crypto_service = CryptoService()
        result = ImportService.process_import(campaign.empresa, campaign, rows, crypto_service)

        messages.success(request, f'{result["created"]} convites importados com sucesso.')
        if result['errors']:
            for error in result['errors'][:5]:
                messages.warning(request, error)

        AuditService.log(request.user, campaign.empresa, 'import_csv',
                         f'Importados {result["created"]} convites', request)

        return redirect('invitations:manage', campaign_id=campaign_id)


class DispatchEmailsView(RHRequiredMixin, View):
    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        invitations = SurveyInvitation.objects.filter(
            campaign=campaign, status='pending'
        ).select_related('campaign', 'empresa')

        crypto_service = CryptoService()
        count = 0

        for invitation in invitations:
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

        messages.success(request, f'{count} e-mails enfileirados para envio.')
        AuditService.log(request.user, campaign.empresa, 'disparo_email',
                         f'Disparados {count} e-mails', request)

        return redirect('invitations:manage', campaign_id=campaign_id)
