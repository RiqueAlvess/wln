from django.views.generic import TemplateView
from apps.core.mixins import DashboardAccessMixin
from app_selectors.campaign_selectors import CampaignSelectors
from app_selectors.dashboard_selectors import DashboardSelectors
from services.risk_service import RiskService


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

        metrics = DashboardSelectors.get_campaign_metrics(campaign)
        dimensoes_scores = DashboardSelectors.get_dimensoes_scores(campaign)
        top_setores = DashboardSelectors.get_top_setores_criticos(campaign)
        distribuicao = RiskService.get_distribuicao_riscos(campaign)
        igrp = RiskService.calcular_igrp(campaign)

        context.update({
            'campaigns': campaigns,
            'campaign': campaign,
            'total_convidados': metrics['total_convidados'],
            'respondidos': metrics['total_respondidos'],
            'adesao': metrics['adesao'],
            'igrp': igrp,
            'pct_risco_alto': distribuicao['percentual_alto'],
            'dimensoes_labels': list(dimensoes_scores.keys()),
            'dimensoes_scores': list(dimensoes_scores.values()),
            'dimensoes_cores': ['#dc3545' if v < 2 else '#ffc107' if v < 3 else '#28a745' for v in dimensoes_scores.values()],
            'top5_setores': top_setores,
        })

        return context
