from django.views.generic import ListView, View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from apps.core.mixins import RHRequiredMixin
from apps.actions.models import PlanoAcao
from apps.surveys.models import Campaign
from services.export_service import ExportService


class PlanoAcaoListView(RHRequiredMixin, ListView):
    model = PlanoAcao
    template_name = 'actions/plano_acao_list.html'
    context_object_name = 'planos'
    paginate_by = 25

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        return PlanoAcao.objects.filter(campaign_id=campaign_id).select_related('dimensao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        context['campaign'] = get_object_or_404(Campaign, id=campaign_id)
        return context


class ExportPlanoAcaoWordView(RHRequiredMixin, View):
    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        planos = PlanoAcao.objects.filter(campaign=campaign).select_related('dimensao')

        doc = ExportService.export_plano_acao_word(campaign, planos)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename=plano_acao_{campaign.nome}.docx'
        doc.save(response)

        return response
