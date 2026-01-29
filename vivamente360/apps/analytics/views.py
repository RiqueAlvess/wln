from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from apps.core.mixins import DashboardAccessMixin
from app_selectors.campaign_selectors import CampaignSelectors
from app_selectors.dashboard_selectors import DashboardSelectors
from services.risk_service import RiskService, CLASSIFICACAO_RISCOS
from services.sector_analysis_service import SectorAnalysisService
from apps.structure.models import Unidade, Setor
from apps.responses.models import SurveyResponse
from apps.analytics.models import SectorAnalysis
from apps.surveys.models import Campaign
import logging

logger = logging.getLogger(__name__)


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
            'classificacao_riscos': CLASSIFICACAO_RISCOS,
        })

        return context


class SectorAnalysisView(DashboardAccessMixin, TemplateView):
    """
    View para exibir análise detalhada de um setor
    """
    template_name = 'analytics/sector_analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        setor_id = self.kwargs.get('setor_id')
        campaign_id = self.kwargs.get('campaign_id')

        setor = get_object_or_404(Setor, id=setor_id)
        campaign = get_object_or_404(Campaign, id=campaign_id)

        # Buscar ou gerar análise
        analysis = SectorAnalysisService.get_analise(setor_id, campaign_id)

        context.update({
            'setor': setor,
            'campaign': campaign,
            'analysis': analysis,
        })

        return context


class GenerateSectorAnalysisView(DashboardAccessMixin, TemplateView):
    """
    View para gerar análise de setor
    """

    def post(self, request, *args, **kwargs):
        setor_id = request.POST.get('setor_id')
        campaign_id = request.POST.get('campaign_id')
        force_regenerate = request.POST.get('force_regenerate') == 'true'

        if not setor_id or not campaign_id:
            return JsonResponse({
                'success': False,
                'error': 'Parâmetros inválidos'
            }, status=400)

        try:
            # Gerar análise
            analysis = SectorAnalysisService.gerar_analise(
                int(setor_id),
                int(campaign_id),
                force_regenerate=force_regenerate
            )

            if not analysis:
                return JsonResponse({
                    'success': False,
                    'error': 'Não foi possível gerar a análise. Verifique se há dados suficientes.'
                }, status=400)

            return JsonResponse({
                'success': True,
                'analysis_id': analysis.id,
                'redirect_url': f'/analytics/sector-analysis/{setor_id}/{campaign_id}/'
            })

        except Exception as e:
            logger.error(f"Erro ao gerar análise: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class SectorAnalysisListView(DashboardAccessMixin, TemplateView):
    """
    View para listar análises de setores
    """
    template_name = 'analytics/sector_analysis_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        campaign_id = self.request.GET.get('campaign')
        campaigns = CampaignSelectors.get_user_campaigns(self.request.user)

        if campaign_id:
            campaign = campaigns.filter(id=campaign_id).first()
        else:
            campaign = campaigns.filter(status='active').first()

        analyses = []
        if campaign:
            # Buscar todas as análises desta campanha
            analyses = SectorAnalysis.objects.filter(
                campaign=campaign,
                empresa=self.request.user.profile.empresas.first()
            ).select_related('setor', 'campaign').order_by('-created_at')

        context.update({
            'campaigns': campaigns,
            'campaign': campaign,
            'analyses': analyses,
        })

        return context
