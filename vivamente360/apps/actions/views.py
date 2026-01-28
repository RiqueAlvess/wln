from django.views.generic import ListView, TemplateView, CreateView, DeleteView, View
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponse
from apps.core.mixins import RHRequiredMixin
from apps.actions.models import ChecklistEtapa, PlanoAcao, Evidencia
from apps.surveys.models import Campaign
from .forms import EvidenciaForm
from services.export_service import ExportService


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


class EvidenciaListView(RHRequiredMixin, ListView):
    model = Evidencia
    template_name = 'actions/evidencias_list.html'
    context_object_name = 'evidencias'
    paginate_by = 20

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        queryset = Evidencia.objects.filter(campaign_id=campaign_id).select_related(
            'checklist_item', 'plano_acao', 'uploaded_by'
        )

        # Filtro por tipo
        tipo_filter = self.request.GET.get('tipo')
        if tipo_filter:
            queryset = queryset.filter(tipo=tipo_filter)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        context['campaign'] = get_object_or_404(Campaign, id=campaign_id)
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        return context


class EvidenciaUploadView(RHRequiredMixin, CreateView):
    model = Evidencia
    form_class = EvidenciaForm
    template_name = 'actions/evidencia_upload.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        campaign_id = self.kwargs['campaign_id']

        # Filtrar checklist items e planos de ação pela campanha
        form.fields['checklist_item'].queryset = ChecklistEtapa.objects.filter(
            campaign_id=campaign_id
        )
        form.fields['plano_acao'].queryset = PlanoAcao.objects.filter(
            campaign_id=campaign_id
        )

        # Tornar ambos os campos opcionais
        form.fields['checklist_item'].required = False
        form.fields['plano_acao'].required = False

        return form

    def form_valid(self, form):
        campaign_id = self.kwargs['campaign_id']
        form.instance.campaign_id = campaign_id
        form.instance.empresa = self.request.user.empresa
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('actions:evidencias', kwargs={'campaign_id': self.kwargs['campaign_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        context['campaign'] = get_object_or_404(Campaign, id=campaign_id)
        return context


class EvidenciaDeleteView(RHRequiredMixin, DeleteView):
    model = Evidencia

    def get_success_url(self):
        return reverse_lazy('actions:evidencias', kwargs={'campaign_id': self.object.campaign.id})


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
