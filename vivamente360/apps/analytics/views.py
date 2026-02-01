from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from apps.core.mixins import DashboardAccessMixin
from apps.core.models import TaskQueue
from app_selectors.campaign_selectors import CampaignSelectors
from app_selectors.dashboard_selectors import DashboardSelectors
from app_selectors.comparison_selectors import ComparisonSelectors
from services.risk_service import RiskService, CLASSIFICACAO_RISCOS
from services.sector_analysis_service import SectorAnalysisService
from services.export_service import ExportService
from apps.structure.models import Unidade, Setor
from apps.responses.models import SurveyResponse
from apps.analytics.models import SectorAnalysis
from apps.surveys.models import Campaign
from tasks.ai_analysis_tasks import enqueue_sector_analysis
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

        # Para líderes, é obrigatório selecionar um setor
        # Não devem ver dados agregados de todos os setores da empresa
        if hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'lideranca':
            if not setor_id:
                # Buscar setores disponíveis para mostrar dropdown
                setores_disponiveis = Setor.objects.filter(
                    id__in=SurveyResponse.objects.filter(campaign=campaign).values_list('setor_id', flat=True).distinct()
                )
                setores_disponiveis = self.filter_setores_by_permission(setores_disponiveis).order_by('nome')

                # Retornar contexto mínimo com mensagem
                context.update({
                    'campaigns': campaigns,
                    'campaign': campaign,
                    'setores_disponiveis': setores_disponiveis,
                    'unidades_disponiveis': Unidade.objects.none(),
                    'requer_selecao_setor': True,
                })
                return context

        # Construir dict de filtros
        filters = {}
        if unidade_id:
            filters['unidade_id'] = unidade_id
        if setor_id:
            filters['setor_id'] = setor_id

        # Buscar unidades e setores disponíveis para esta campanha
        # Filtrar por permissões do usuário (Liderança vê apenas suas unidades/setores)
        unidades_disponiveis = Unidade.objects.filter(
            id__in=SurveyResponse.objects.filter(campaign=campaign).values_list('unidade_id', flat=True).distinct()
        )
        unidades_disponiveis = self.filter_unidades_by_permission(unidades_disponiveis).order_by('nome')

        # Se uma unidade foi selecionada, filtrar setores por ela
        if unidade_id:
            setores_disponiveis = Setor.objects.filter(
                unidade_id=unidade_id,
                id__in=SurveyResponse.objects.filter(campaign=campaign).values_list('setor_id', flat=True).distinct()
            )
        else:
            setores_disponiveis = Setor.objects.filter(
                id__in=SurveyResponse.objects.filter(campaign=campaign).values_list('setor_id', flat=True).distinct()
            )

        # Aplicar filtro de permissão (Liderança vê apenas seus setores)
        setores_disponiveis = self.filter_setores_by_permission(setores_disponiveis).order_by('nome')

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

        # Validar permissão: usuário pode acessar este setor?
        setores_permitidos = self.get_setores_permitidos()
        if setor not in setores_permitidos:
            messages.error(self.request, 'Você não tem permissão para acessar análises deste setor.')
            return redirect('analytics:sector_analysis_list')

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
    template_name = 'analytics/generate_sector_analysis.html'

    def get(self, request, *args, **kwargs):
        """Exibe página de seleção de setor para gerar análise"""
        campaigns = CampaignSelectors.get_user_campaigns(request.user)
        campaign_id = request.GET.get('campaign')

        if campaign_id:
            campaign = campaigns.filter(id=campaign_id).first()
        else:
            campaign = campaigns.filter(status='active').first()

        if not campaign:
            messages.error(request, 'Selecione uma campanha válida.')
            return redirect('analytics:sector_analysis_list')

        # Buscar setores com respostas nesta campanha
        setores_com_respostas = Setor.objects.filter(
            id__in=SurveyResponse.objects.filter(campaign=campaign).values_list('setor_id', flat=True).distinct()
        ).select_related('unidade')

        # Filtrar por permissões do usuário (Liderança vê apenas seus setores)
        setores_com_respostas = self.filter_setores_by_permission(setores_com_respostas).order_by('unidade__nome', 'nome')

        context = {
            'campaigns': campaigns,
            'campaign': campaign,
            'setores': setores_com_respostas,
        }

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """Enfileira geração de análise"""
        try:
            setor_id = request.POST.get('setor_id')
            campaign_id = request.POST.get('campaign_id')

            if not setor_id or not campaign_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Setor e campanha são obrigatórios'
                }, status=400)

            # Validar setor e campanha existem
            setor = get_object_or_404(Setor, id=setor_id)
            campaign = get_object_or_404(Campaign, id=campaign_id)

            # Validar permissão: usuário pode acessar este setor?
            setores_permitidos = self.get_setores_permitidos()
            if setor not in setores_permitidos:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Você não tem permissão para gerar análise deste setor'
                }, status=403)

            # Verificar se já existe análise recente (últimas 24h)
            recent_analysis = SectorAnalysis.objects.filter(
                setor=setor,
                campaign=campaign,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).first()

            if recent_analysis:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Análise recente encontrada',
                    'analysis_id': recent_analysis.id,
                    'redirect_url': f'/dashboard/sector-analysis/{setor_id}/?campaign={campaign_id}'
                })

            # Enfileirar análise
            task = enqueue_sector_analysis(
                setor_id=setor_id,
                campaign_id=campaign_id,
                user_id=request.user.id if request.user.is_authenticated else None
            )

            return JsonResponse({
                'status': 'queued',
                'message': 'Análise enfileirada para processamento',
                'task_id': task.id,
                'poll_url': f'/dashboard/sector-analysis/status/{task.id}/'
            })

        except Exception as e:
            logger.error(f"Erro ao enfileirar análise: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


class CheckAnalysisStatusView(View):
    """Verifica status de análise em processamento"""

    def get(self, request, task_id):
        try:
            task = get_object_or_404(TaskQueue, id=task_id)

            response_data = {
                'task_id': task.id,
                'status': task.status,
                'attempts': task.attempts,
                'created_at': task.created_at.isoformat()
            }

            if task.status == 'completed':
                analysis_id = task.payload.get('analysis_id')
                if analysis_id:
                    analysis = SectorAnalysis.objects.get(id=analysis_id)
                    response_data['redirect_url'] = f'/dashboard/sector-analysis/{analysis.setor.id}/?campaign={analysis.campaign.id}'

            elif task.status == 'failed':
                response_data['error'] = task.error_message

            return JsonResponse(response_data)

        except TaskQueue.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Task não encontrada'
            }, status=404)


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
            # Buscar empresa do usuário com fallback seguro
            if hasattr(self.request.user, 'profile') and self.request.user.profile.empresas.exists():
                empresa = self.request.user.profile.empresas.first()
            else:
                # Fallback: buscar pela empresa da campanha
                empresa = campaign.empresa

            # Buscar todas as análises desta campanha
            analyses = SectorAnalysis.objects.filter(
                campaign=campaign,
                empresa=empresa
            ).select_related('setor', 'campaign')

            # Filtrar análises por setores permitidos (Liderança vê apenas seus setores)
            setores_permitidos = self.get_setores_permitidos()
            analyses = analyses.filter(setor__in=setores_permitidos).order_by('-created_at')

        context.update({
            'campaigns': campaigns,
            'campaign': campaign,
            'analyses': analyses,
        })

        return context


class CampaignComparisonView(DashboardAccessMixin, TemplateView):
    """
    View para comparação entre duas campanhas da mesma empresa
    """
    template_name = 'analytics/campaign_comparison.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        campaigns = CampaignSelectors.get_user_campaigns(self.request.user)

        # Obter campanhas selecionadas para comparação
        campaign1_id = self.request.GET.get('campaign1')
        campaign2_id = self.request.GET.get('campaign2')

        # Verificar se há campanhas suficientes
        if campaigns.count() < 2:
            context.update({
                'campaigns': campaigns,
                'error': 'É necessário ter pelo menos 2 campanhas para realizar a comparação.',
                'campaign1': None,
                'campaign2': None,
            })
            return context

        # Se não houver seleção, usar as duas campanhas mais recentes
        if not campaign1_id or not campaign2_id:
            recent_campaigns = campaigns.order_by('-created_at')[:2]
            if recent_campaigns.count() >= 2:
                campaign1 = recent_campaigns[1]  # Mais antiga
                campaign2 = recent_campaigns[0]  # Mais recente
            else:
                context.update({
                    'campaigns': campaigns,
                    'campaign1': None,
                    'campaign2': None,
                })
                return context
        else:
            campaign1 = campaigns.filter(id=campaign1_id).first()
            campaign2 = campaigns.filter(id=campaign2_id).first()

            if not campaign1 or not campaign2:
                context.update({
                    'campaigns': campaigns,
                    'error': 'Campanhas inválidas selecionadas.',
                    'campaign1': None,
                    'campaign2': None,
                })
                return context

        # Verificar se as campanhas são da mesma empresa
        if campaign1.empresa != campaign2.empresa:
            context.update({
                'campaigns': campaigns,
                'error': 'Só é possível comparar campanhas da mesma empresa.',
                'campaign1': campaign1,
                'campaign2': campaign2,
            })
            return context

        # Buscar dados de comparação
        try:
            summary = ComparisonSelectors.get_evolution_summary(campaign1, campaign2)
            dimensions = ComparisonSelectors.get_evolution_by_dimension(campaign1, campaign2)
            sectors = ComparisonSelectors.get_top_sectors_evolution(campaign1, campaign2)
            sentiment = ComparisonSelectors.get_sentiment_evolution(campaign1, campaign2)

            # Gerar análise de IA
            evolution_data = {
                'summary': summary,
                'dimensions': dimensions,
                'sectors': sectors,
            }
            ai_analysis = ComparisonSelectors.generate_ai_analysis(campaign1, campaign2, evolution_data)

            context.update({
                'campaigns': campaigns,
                'campaign1': campaign1,
                'campaign2': campaign2,
                'summary': summary,
                'dimensions': dimensions,
                'sectors': sectors,
                'sentiment': sentiment,
                'ai_analysis': ai_analysis,
            })

        except Exception as e:
            logger.error(f"Erro ao gerar comparação: {e}")
            context.update({
                'campaigns': campaigns,
                'campaign1': campaign1,
                'campaign2': campaign2,
                'error': f'Erro ao gerar comparação: {str(e)}',
            })

        return context


class ExportCampaignComparisonView(DashboardAccessMixin, TemplateView):
    """
    View para exportar comparação entre campanhas em Word via fila de processamento
    """

    def get(self, request, *args, **kwargs):
        from apps.core.models import TaskQueue
        from django.http import JsonResponse

        campaign1_id = request.GET.get('campaign1')
        campaign2_id = request.GET.get('campaign2')

        if not campaign1_id or not campaign2_id:
            return JsonResponse({'error': 'Selecione duas campanhas para comparar.'}, status=400)

        campaigns = CampaignSelectors.get_user_campaigns(request.user)
        campaign1 = campaigns.filter(id=campaign1_id).first()
        campaign2 = campaigns.filter(id=campaign2_id).first()

        if not campaign1 or not campaign2:
            return JsonResponse({'error': 'Campanhas inválidas.'}, status=400)

        try:
            # Criar task de processamento
            task = TaskQueue.objects.create(
                task_type='export_campaign_comparison',
                payload={
                    'campaign1_id': int(campaign1_id),
                    'campaign2_id': int(campaign2_id),
                },
                user=request.user,
                empresa=request.user.profile.empresa if hasattr(request.user, 'profile') else None,
                progress_message='Preparando comparação de campanhas...'
            )

            return JsonResponse({
                'task_id': task.id,
                'message': 'Exportação iniciada. Você será notificado quando estiver pronta.',
                'status_url': f'/api/tasks/{task.id}/'
            })

        except Exception as e:
            logger.error(f"Erro ao criar task de comparação: {e}")
            return JsonResponse({'error': f'Erro ao exportar relatório: {str(e)}'}, status=500)


# ============================================================================
# VIEWS - MATRIZ DE RISCO PSICOSSOCIAL NR-1
# ============================================================================

class PsychosocialRiskMatrixView(DashboardAccessMixin, TemplateView):
    """View principal da Matriz de Risco Psicossocial (NR-1)"""
    template_name = 'analytics/psychosocial_risk_matrix.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        campaigns = CampaignSelectors.get_user_campaigns(self.request.user)
        campaign_id = self.request.GET.get('campaign') or kwargs.get('campaign_id')

        if campaign_id:
            campaign = campaigns.filter(id=campaign_id).first()
        else:
            campaign = campaigns.filter(status='active').first()

        if not campaign:
            context['campaigns'] = campaigns
            context['campaign'] = None
            context['error'] = 'Nenhuma campanha disponível'
            return context

        # Importar serviços de risco
        from services.risk_assessment_service import RiskAssessmentService

        try:
            # Executar avaliação completa
            processar_ia = self.request.GET.get('processar_ia', 'true').lower() == 'true'
            avaliacao = RiskAssessmentService.avaliar_campanha_completa(
                campaign,
                processar_ia=processar_ia
            )

            # Preparar dados para visualização
            matriz = avaliacao['matriz_ajustada'] if avaliacao.get('processou_ia') else avaliacao['matriz_base']

            context.update({
                'campaigns': campaigns,
                'campaign': campaign,
                'avaliacao': avaliacao,
                'matriz': matriz,
                'resumo': avaliacao['resumo'],
                'alertas_criticos': avaliacao.get('alertas_criticos', []),
                'processou_ia': avaliacao.get('processou_ia', False),
                'total_fatores': matriz['resumo']['total_fatores'],
            })

        except Exception as e:
            logger.error(f"Erro ao gerar matriz de risco: {e}", exc_info=True)
            context['error'] = f'Erro ao processar matriz de risco: {str(e)}'
            context['campaigns'] = campaigns
            context['campaign'] = campaign

        return context


class SectorRiskDetailView(DashboardAccessMixin, TemplateView):
    """View detalhada de risco de um setor específico"""
    template_name = 'analytics/sector_risk_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        campaign_id = kwargs.get('campaign_id')
        setor_id = kwargs.get('setor_id')

        campaign = get_object_or_404(Campaign, id=campaign_id)
        setor = get_object_or_404(Setor, id=setor_id)

        # Verificar permissão de campanha
        campaigns = CampaignSelectors.get_user_campaigns(self.request.user)
        if campaign not in campaigns:
            messages.error(self.request, 'Você não tem permissão para acessar esta campanha.')
            return redirect('analytics:dashboard')

        # Verificar permissão de setor (Liderança vê apenas seus setores)
        setores_permitidos = self.get_setores_permitidos()
        if setor not in setores_permitidos:
            messages.error(self.request, 'Você não tem permissão para acessar dados deste setor.')
            return redirect('analytics:psychosocial_risk_matrix')

        from services.risk_assessment_service import RiskAssessmentService

        try:
            # Avaliar setor
            processar_ia = self.request.GET.get('processar_ia', 'true').lower() == 'true'
            avaliacao_setor = RiskAssessmentService.avaliar_setor_especifico(
                campaign,
                setor,
                processar_ia=processar_ia
            )

            context.update({
                'campaign': campaign,
                'setor': setor,
                'avaliacao': avaliacao_setor,
                'fatores': avaliacao_setor['fatores'],
                'fatores_criticos': avaliacao_setor['fatores_criticos'],
                'resumo': avaliacao_setor['resumo'],
                'analise_ia': avaliacao_setor.get('analise_ia'),
                'processou_ia': avaliacao_setor.get('processou_ia', False),
            })

        except Exception as e:
            logger.error(f"Erro ao avaliar setor: {e}", exc_info=True)
            context['error'] = f'Erro ao processar análise do setor: {str(e)}'
            context['campaign'] = campaign
            context['setor'] = setor

        return context


class ExportRiskMatrixExcelView(DashboardAccessMixin, TemplateView):
    """View para exportar matriz de risco em Excel via fila de processamento"""

    def get(self, request, *args, **kwargs):
        from apps.core.models import TaskQueue
        from django.http import JsonResponse

        campaign_id = kwargs.get('campaign_id')
        campaign = get_object_or_404(Campaign, id=campaign_id)

        # Verificar permissão
        campaigns = CampaignSelectors.get_user_campaigns(request.user)
        if campaign not in campaigns:
            return JsonResponse({'error': 'Você não tem permissão para acessar esta campanha.'}, status=403)

        try:
            # Criar task de processamento
            task = TaskQueue.objects.create(
                task_type='export_risk_matrix_excel',
                payload={
                    'campaign_id': campaign_id,
                },
                user=request.user,
                empresa=request.user.profile.empresa if hasattr(request.user, 'profile') else None,
                progress_message='Preparando exportação de matriz de risco...'
            )

            return JsonResponse({
                'task_id': task.id,
                'message': 'Exportação iniciada. Você será notificado quando estiver pronta.',
                'status_url': f'/api/tasks/{task.id}/'
            })

        except Exception as e:
            logger.error(f"Erro ao criar task de matriz para Excel: {e}", exc_info=True)
            return JsonResponse({'error': f'Erro ao exportar para Excel: {str(e)}'}, status=500)


class ExportRiskMatrixPGRView(DashboardAccessMixin, TemplateView):
    """View para exportar relatório PGR (Programa de Gerenciamento de Riscos) via fila de processamento"""

    def get(self, request, *args, **kwargs):
        from apps.core.models import TaskQueue
        from django.http import JsonResponse

        campaign_id = kwargs.get('campaign_id')
        campaign = get_object_or_404(Campaign, id=campaign_id)

        # Verificar permissão
        campaigns = CampaignSelectors.get_user_campaigns(request.user)
        if campaign not in campaigns:
            return JsonResponse({'error': 'Você não tem permissão para acessar esta campanha.'}, status=403)

        try:
            # Criar task de processamento
            task = TaskQueue.objects.create(
                task_type='export_pgr_document',
                payload={
                    'campaign_id': campaign_id,
                },
                user=request.user,
                empresa=request.user.profile.empresa if hasattr(request.user, 'profile') else None,
                progress_message='Preparando relatório PGR...'
            )

            return JsonResponse({
                'task_id': task.id,
                'message': 'Exportação iniciada. Você será notificado quando estiver pronta.',
                'status_url': f'/api/tasks/{task.id}/'
            })

        except Exception as e:
            logger.error(f"Erro ao criar task de PGR: {e}", exc_info=True)
            return JsonResponse({'error': f'Erro ao exportar relatório PGR: {str(e)}'}, status=500)
