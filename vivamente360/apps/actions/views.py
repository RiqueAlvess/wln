from django.views.generic import ListView, TemplateView
from django.shortcuts import get_object_or_404
from apps.core.mixins import RHRequiredMixin
from apps.actions.models import ChecklistEtapa, PlanoAcao
from apps.surveys.models import Campaign


class ChecklistView(RHRequiredMixin, ListView):
    model = ChecklistEtapa
    template_name = 'actions/checklist.html'
    context_object_name = 'items'

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        return ChecklistEtapa.objects.filter(campaign_id=campaign_id).order_by('etapa', 'item_ordem')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        context['campaign'] = get_object_or_404(Campaign, id=campaign_id)
        return context


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
