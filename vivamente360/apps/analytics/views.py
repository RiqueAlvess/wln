from django.views.generic import TemplateView
from apps.core.mixins import DashboardAccessMixin
from app_selectors.campaign_selectors import CampaignSelectors
from app_selectors.dashboard_selectors import DashboardSelectors
from services.risk_service import RiskService
from apps.structure.models import Unidade, Setor
from apps.responses.models import SurveyResponse


class DashboardView(DashboardAccessMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        campaigns = CampaignSelectors.get_user_campaigns(self.request.user)
        campaign_id = self.request.GET.get('campaign')

        if campaign_id:
            campaign = campaigns.filter(id=campaign_id).first()
        else:
            campaign = campaigns.filter(status='active').first()

        if not campaign:
            context['campaigns'] = campaigns
            context['campaign'] = None
            return context

        # Obter parâmetros de filtro
        unidade_id = self.request.GET.get('unidade')
        setor_id = self.request.GET.get('setor')

        # Construir dict de filtros
        filters = {}
        if unidade_id:
            filters['unidade_id'] = unidade_id
        if setor_id:
            filters['setor_id'] = setor_id

        # Buscar unidades e setores disponíveis para esta campanha
        unidades_disponiveis = Unidade.objects.filter(
            id__in=SurveyResponse.objects.filter(campaign=campaign).values_list('unidade_id', flat=True).distinct()
        ).order_by('nome')

        # Se uma unidade foi selecionada, filtrar setores por ela
        if unidade_id:
            setores_disponiveis = Setor.objects.filter(
                unidade_id=unidade_id,
                id__in=SurveyResponse.objects.filter(campaign=campaign).values_list('setor_id', flat=True).distinct()
            ).order_by('nome')
        else:
            setores_disponiveis = Setor.objects.filter(
                id__in=SurveyResponse.objects.filter(campaign=campaign).values_list('setor_id', flat=True).distinct()
            ).order_by('nome')

        # Buscar dados com filtros aplicados
        metrics = DashboardSelectors.get_campaign_metrics(campaign, filters)
        dimensoes_scores = DashboardSelectors.get_dimensoes_scores(campaign, filters)
        top_setores = DashboardSelectors.get_top_setores_criticos(campaign, filters=filters)
        distribuicao = RiskService.get_distribuicao_riscos(campaign, filters)
        igrp = RiskService.calcular_igrp(campaign, filters)
        demografico_genero = DashboardSelectors.get_demografico_genero(campaign, filters)
        demografico_faixa = DashboardSelectors.get_demografico_faixa_etaria(campaign, filters)
        heatmap_data = DashboardSelectors.get_heatmap_data(campaign, filters)
        scores_por_genero = DashboardSelectors.get_scores_por_genero(campaign, filters)
        scores_por_faixa_etaria = DashboardSelectors.get_scores_por_faixa_etaria(campaign, filters)
        top_grupos_criticos = DashboardSelectors.get_top_grupos_demograficos_criticos(campaign, filters=filters)

        context.update({
            'campaigns': campaigns,
            'campaign': campaign,
            'unidades_disponiveis': unidades_disponiveis,
            'setores_disponiveis': setores_disponiveis,
            'unidade_selecionada': unidade_id,
            'setor_selecionado': setor_id,
            'total_convidados': metrics['total_convidados'],
            'respondidos': metrics['total_respondidos'],
            'adesao': metrics['adesao'],
            'igrp': igrp,
            'pct_risco_alto': distribuicao['percentual_alto'],
            'dimensoes_labels': list(dimensoes_scores.keys()),
            'dimensoes_scores': list(dimensoes_scores.values()),
            'dimensoes_cores': ['#dc3545' if v < 2 else '#ffc107' if v < 3 else '#28a745' for v in dimensoes_scores.values()],
            'top5_setores': top_setores,
            'distribuicao_values': [
                distribuicao.get('aceitavel', 0),
                distribuicao.get('moderado', 0),
                distribuicao.get('importante', 0),
                distribuicao.get('critico', 0)
            ],
            'genero_labels': demografico_genero['labels'],
            'genero_values': demografico_genero['values'],
            'faixa_etaria_labels': demografico_faixa['labels'],
            'faixa_etaria_values': demografico_faixa['values'],
            'heatmap_data': heatmap_data,
            'scores_por_genero': scores_por_genero,
            'scores_por_faixa_etaria': scores_por_faixa_etaria,
            'top_grupos_criticos': top_grupos_criticos,
        })

        return context
