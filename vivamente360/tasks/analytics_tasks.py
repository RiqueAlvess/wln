from apps.analytics.models import (
    DimTempo, DimEstrutura, DimDemografia, DimDimensaoHSE,
    FactScoreDimensao, FactIndicadorCampanha
)
from apps.responses.models import SurveyResponse
from services.score_service import ScoreService
from services.risk_service import RiskService


def rebuild_campaign_analytics(campaign):
    responses = SurveyResponse.objects.filter(campaign=campaign).select_related(
        'unidade', 'setor', 'cargo'
    )

    for response in responses:
        dim_tempo, _ = DimTempo.objects.get_or_create(
            data=response.created_at.date(),
            defaults={
                'ano': response.created_at.year,
                'mes': response.created_at.month,
                'trimestre': (response.created_at.month - 1) // 3 + 1,
                'semana_ano': response.created_at.isocalendar()[1],
                'dia_semana': response.created_at.weekday(),
                'nome_mes': response.created_at.strftime('%B')
            }
        )

        dim_estrutura, _ = DimEstrutura.objects.get_or_create(
            empresa_id=campaign.empresa.id,
            empresa_nome=campaign.empresa.nome,
            unidade_id=response.unidade.id,
            unidade_nome=response.unidade.nome,
            setor_id=response.setor.id,
            setor_nome=response.setor.nome,
            cargo_id=response.cargo.id,
            cargo_nome=response.cargo.nome,
            cargo_nivel=response.cargo.nivel
        )

        dim_demografia, _ = DimDemografia.objects.get_or_create(
            faixa_etaria=response.faixa_etaria,
            tempo_empresa=response.tempo_empresa,
            genero=response.genero
        )

        scores = ScoreService.processar_resposta_completa(response.respostas)

        for dimensao_codigo, data in scores.items():
            dim_hse, _ = DimDimensaoHSE.objects.get_or_create(
                codigo=dimensao_codigo,
                defaults={
                    'nome': dimensao_codigo.replace('_', ' ').title(),
                    'tipo': 'negativo' if dimensao_codigo in ScoreService.DIMENSOES_NEGATIVAS else 'positivo'
                }
            )

            FactScoreDimensao.objects.create(
                campaign=campaign,
                dim_tempo=dim_tempo,
                dim_estrutura=dim_estrutura,
                dim_demografia=dim_demografia,
                dim_hse=dim_hse,
                score_medio=data['score'],
                probabilidade=data['probabilidade'],
                severidade=2,
                nivel_risco=data['nivel'],
                classificacao=data['interpretacao'],
                cor=data['cor'],
                total_respostas=1
            )
