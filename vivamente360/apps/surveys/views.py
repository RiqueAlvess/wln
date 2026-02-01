from django.views.generic import ListView, CreateView, DetailView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from apps.core.mixins import RHRequiredMixin
from apps.surveys.models import Campaign
from app_selectors.campaign_selectors import CampaignSelectors


class CampaignListView(RHRequiredMixin, ListView):
    model = Campaign
    template_name = 'campaigns/list.html'
    context_object_name = 'campaigns'
    paginate_by = 25

    def get_queryset(self):
        return CampaignSelectors.get_user_campaigns(self.request.user)


class CampaignCreateView(RHRequiredMixin, CreateView):
    model = Campaign
    template_name = 'campaigns/create.html'
    fields = ['nome', 'descricao', 'empresa', 'data_inicio', 'data_fim', 'status']
    success_url = reverse_lazy('surveys:list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Filtrar empresas disponíveis baseado nas permissões do usuário
        if self.request.user.is_superuser:
            # Superusuário vê todas as empresas
            pass
        elif hasattr(self.request.user, 'profile'):
            # RH vê apenas suas empresas vinculadas
            form.fields['empresa'].queryset = self.request.user.profile.empresas.all()
        else:
            # Usuário sem perfil não vê nenhuma empresa
            form.fields['empresa'].queryset = form.fields['empresa'].queryset.none()

        # Adicionar classes CSS aos widgets
        form.fields['empresa'].widget.attrs.update({
            'class': 'form-select form-select-lg',
            'required': 'required'
        })
        form.fields['nome'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Ex: Avaliação Anual 2024'
        })
        form.fields['descricao'].widget.attrs.update({
            'class': 'form-control',
            'rows': '4',
            'placeholder': 'Descreva os objetivos e contexto desta campanha...'
        })
        form.fields['data_inicio'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'type': 'date'
        })
        form.fields['data_fim'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'type': 'date'
        })

        # Ocultar campo status (definido automaticamente como 'draft')
        form.fields['status'].widget = form.fields['status'].hidden_widget()
        form.fields['status'].initial = 'draft'

        return form

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class CampaignDetailView(RHRequiredMixin, DetailView):
    model = Campaign
    template_name = 'campaigns/detail.html'
    context_object_name = 'campaign'

    def get_queryset(self):
        return CampaignSelectors.get_user_campaigns(self.request.user)


class CampaignManageStatusView(RHRequiredMixin, View):
    """
    View para gerenciar o status de uma campanha.
    GET: Exibe formulário de confirmação
    POST: Processa alteração de status
    """
    template_name = 'campaigns/manage_status.html'

    def get(self, request, pk):
        campaign = get_object_or_404(
            CampaignSelectors.get_user_campaigns(request.user),
            pk=pk
        )

        # Contar convites ativos
        convites_info = campaign.contar_convites_ativos()

        context = {
            'campaign': campaign,
            'convites_pendentes': convites_info['pendentes'],
            'convites_enviados': convites_info['enviados'],
            'total_convites_ativos': convites_info['total_ativos'],
        }

        return render(request, self.template_name, context)

    def post(self, request, pk):
        campaign = get_object_or_404(
            CampaignSelectors.get_user_campaigns(request.user),
            pk=pk
        )

        novo_status = request.POST.get('status')

        # Validar status
        status_validos = [choice[0] for choice in Campaign.STATUS_CHOICES]
        if novo_status not in status_validos:
            messages.error(request, 'Status inválido.')
            return redirect('surveys:manage_status', pk=campaign.pk)

        # Se status é 'closed', usar método encerrar()
        if novo_status == 'closed':
            resultado = campaign.encerrar()

            if resultado['success']:
                messages.success(
                    request,
                    f'Campanha encerrada com sucesso! {resultado["invalidated_count"]} '
                    f'convite(s) invalidado(s).'
                )
            else:
                messages.warning(request, resultado['message'])

        else:
            # Para outros status, apenas atualizar
            campaign.status = novo_status
            campaign.save()

            status_label = dict(Campaign.STATUS_CHOICES).get(novo_status)
            messages.success(
                request,
                f'Status da campanha alterado para "{status_label}".'
            )

        return redirect('surveys:detail', pk=campaign.pk)
