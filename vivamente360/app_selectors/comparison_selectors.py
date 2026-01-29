from django.db.models import Count, Avg
from apps.responses.models import SurveyResponse
from apps.invitations.models import SurveyInvitation
from services.score_service import ScoreService
from services.risk_service import RiskService
from collections import defaultdict


class ComparisonSelectors:
    """
    Seletores para comparação entre duas campanhas da mesma empresa.
    """

    @staticmethod
    def get_evolution_summary(campaign1, campaign2):
        """
        Retorna um resumo comparativo das métricas principais entre duas campanhas.

        Args:
            campaign1: Campanha base (antiga)
            campaign2: Campanha nova

        Returns:
            dict com métricas comparativas
        """
        # Métricas da campanha 1
        metrics1 = ComparisonSelectors._get_campaign_metrics(campaign1)

        # Métricas da campanha 2
        metrics2 = ComparisonSelectors._get_campaign_metrics(campaign2)

        # Calcular variações
        variacao_adesao = metrics2['adesao'] - metrics1['adesao']
        variacao_igrp = metrics2['igrp'] - metrics1['igrp']
        variacao_risco_alto = metrics2['pct_risco_alto'] - metrics1['pct_risco_alto']
        variacao_respostas = metrics2['total_respostas'] - metrics1['total_respostas']

        return {
            'campaign1': {
                'nome': campaign1.nome,
                'adesao': metrics1['adesao'],
                'igrp': metrics1['igrp'],
                'pct_risco_alto': metrics1['pct_risco_alto'],
                'total_respostas': metrics1['total_respostas']
            },
            'campaign2': {
                'nome': campaign2.nome,
                'adesao': metrics2['adesao'],
                'igrp': metrics2['igrp'],
                'pct_risco_alto': metrics2['pct_risco_alto'],
                'total_respostas': metrics2['total_respostas']
            },
            'variacao': {
                'adesao': round(variacao_adesao, 2),
                'igrp': round(variacao_igrp, 2),
                'pct_risco_alto': round(variacao_risco_alto, 2),
                'total_respostas': variacao_respostas
            }
        }

    @staticmethod
    def _get_campaign_metrics(campaign):
        """
        Calcula métricas de uma campanha específica.
        """
        # Total de convites e respostas
        total_convidados = SurveyInvitation.objects.filter(campaign=campaign).count()
        total_respostas = SurveyResponse.objects.filter(campaign=campaign).count()

        # Taxa de adesão
        adesao = round((total_respostas / total_convidados * 100), 2) if total_convidados > 0 else 0

        # IGRP
        igrp = RiskService.calcular_igrp(campaign)

        # Distribuição de riscos
        distribuicao = RiskService.get_distribuicao_riscos(campaign)

        # Percentual de risco alto/crítico (importante + crítico)
        total_avaliacoes = sum(distribuicao.values())
        riscos_altos = distribuicao.get('importante', 0) + distribuicao.get('critico', 0)
        pct_risco_alto = round((riscos_altos / total_avaliacoes * 100), 2) if total_avaliacoes > 0 else 0

        return {
            'total_respostas': total_respostas,
            'adesao': adesao,
            'igrp': igrp,
            'pct_risco_alto': pct_risco_alto
        }

    @staticmethod
    def get_evolution_by_dimension(campaign1, campaign2):
        """
        Retorna a evolução dos scores por dimensão HSE-IT.

        Returns:
            dict com scores médios por dimensão para cada campanha
        """
        # Scores por dimensão para cada campanha
        scores1 = ComparisonSelectors._get_dimensoes_scores(campaign1)
        scores2 = ComparisonSelectors._get_dimensoes_scores(campaign2)

        # Nome das dimensões em português
        dimensoes_nomes = {
            'demandas': 'Demandas',
            'controle': 'Controle',
            'apoio_chefia': 'Apoio Chefia',
            'apoio_colegas': 'Apoio Colegas',
            'relacionamentos': 'Relacionamentos',
            'cargo': 'Cargo',
            'comunicacao_mudancas': 'Comunicação'
        }

        result = []
        for dimensao_key, dimensao_nome in dimensoes_nomes.items():
            score1 = scores1.get(dimensao_key, 0)
            score2 = scores2.get(dimensao_key, 0)
            variacao = round(score2 - score1, 2)

            # Tendência (melhora/piora/estável)
            # Para dimensões negativas (demandas, relacionamentos), diminuir é melhor
            dimensoes_negativas = ['demandas', 'relacionamentos']

            if abs(variacao) < 0.1:
                tendencia = 'estavel'
            elif dimensao_key in dimensoes_negativas:
                tendencia = 'melhora' if variacao < 0 else 'piora'
            else:
                tendencia = 'melhora' if variacao > 0 else 'piora'

            result.append({
                'dimensao': dimensao_nome,
                'score_c1': score1,
                'score_c2': score2,
                'variacao': variacao,
                'variacao_pct': round((variacao / score1 * 100), 1) if score1 > 0 else 0,
                'tendencia': tendencia
            })

        return result

    @staticmethod
    def _get_dimensoes_scores(campaign):
        """
        Calcula scores médios por dimensão para uma campanha.
        """
        responses = SurveyResponse.objects.filter(campaign=campaign)

        dimensoes_data = {dim: [] for dim in ScoreService.DIMENSOES.keys()}

        for response in responses:
            for dimensao in ScoreService.DIMENSOES.keys():
                score = ScoreService.calcular_score_dimensao(response.respostas, dimensao)
                dimensoes_data[dimensao].append(score)

        result = {}
        for dimensao, scores in dimensoes_data.items():
            if scores:
                result[dimensao] = round(sum(scores) / len(scores), 2)
            else:
                result[dimensao] = 0.0

        return result

    @staticmethod
    def get_top_sectors_evolution(campaign1, campaign2, limit=5):
        """
        Retorna os setores que mais melhoraram e os que pioraram.

        Returns:
            dict com 'melhoraram' e 'pioraram'
        """
        # IGRP por setor para cada campanha
        setores_c1 = ComparisonSelectors._get_igrp_by_sector(campaign1)
        setores_c2 = ComparisonSelectors._get_igrp_by_sector(campaign2)

        # Calcular evolução
        evolucao = []
        for setor_id, setor_data in setores_c2.items():
            if setor_id in setores_c1:
                igrp1 = setores_c1[setor_id]['igrp']
                igrp2 = setor_data['igrp']
                variacao = igrp2 - igrp1

                evolucao.append({
                    'setor': setor_data['nome'],
                    'igrp_c1': igrp1,
                    'igrp_c2': igrp2,
                    'variacao': round(variacao, 2)
                })

        # Ordenar por variação (negativo é melhora, positivo é piora)
        evolucao.sort(key=lambda x: x['variacao'])

        melhoraram = [s for s in evolucao if s['variacao'] < -0.1][:limit]
        pioraram = [s for s in evolucao if s['variacao'] > 0.1]
        pioraram.reverse()  # Inverter para mostrar os piores primeiro
        pioraram = pioraram[:limit]

        return {
            'melhoraram': melhoraram,
            'pioraram': pioraram
        }

    @staticmethod
    def _get_igrp_by_sector(campaign):
        """
        Calcula IGRP por setor para uma campanha.

        Returns:
            dict {setor_id: {'nome': str, 'igrp': float}}
        """
        responses = SurveyResponse.objects.filter(campaign=campaign).select_related('setor')

        setor_scores = defaultdict(list)
        setor_nomes = {}

        for response in responses:
            setor_id = response.setor.id
            setor_nomes[setor_id] = response.setor.nome

            # Calcular scores de todas as dimensões
            scores = ScoreService.processar_resposta_completa(response.respostas)

            # Adicionar todos os níveis de risco
            for dimensao, data in scores.items():
                setor_scores[setor_id].append(data['nivel'])

        # Calcular IGRP médio por setor
        result = {}
        for setor_id, niveis in setor_scores.items():
            igrp = round(sum(niveis) / len(niveis), 2) if niveis else 0
            result[setor_id] = {
                'nome': setor_nomes[setor_id],
                'igrp': igrp
            }

        return result

    @staticmethod
    def get_sentiment_evolution(campaign1, campaign2):
        """
        Retorna a evolução do sentimento entre campanhas.

        Returns:
            dict com scores de sentimento e categorias mais mencionadas
        """
        # Análise de sentimento campanha 1
        responses1 = SurveyResponse.objects.filter(
            campaign=campaign1,
            sentimento_score__isnull=False
        )

        sentimentos1 = [r.sentimento_score for r in responses1]
        avg_sentimento1 = round(sum(sentimentos1) / len(sentimentos1), 3) if sentimentos1 else 0

        # Categorias campanha 1
        categorias1 = defaultdict(int)
        for r in responses1:
            if r.sentimento_categorias:
                for cat in r.sentimento_categorias:
                    categorias1[cat] += 1

        # Análise de sentimento campanha 2
        responses2 = SurveyResponse.objects.filter(
            campaign=campaign2,
            sentimento_score__isnull=False
        )

        sentimentos2 = [r.sentimento_score for r in responses2]
        avg_sentimento2 = round(sum(sentimentos2) / len(sentimentos2), 3) if sentimentos2 else 0

        # Categorias campanha 2
        categorias2 = defaultdict(int)
        for r in responses2:
            if r.sentimento_categorias:
                for cat in r.sentimento_categorias:
                    categorias2[cat] += 1

        # Top categorias
        top_categorias1 = sorted(categorias1.items(), key=lambda x: x[1], reverse=True)[:5]
        top_categorias2 = sorted(categorias2.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'campaign1': {
                'avg_score': avg_sentimento1,
                'total_comentarios': len(sentimentos1),
                'top_categorias': [{'categoria': cat, 'count': count} for cat, count in top_categorias1]
            },
            'campaign2': {
                'avg_score': avg_sentimento2,
                'total_comentarios': len(sentimentos2),
                'top_categorias': [{'categoria': cat, 'count': count} for cat, count in top_categorias2]
            },
            'variacao_score': round(avg_sentimento2 - avg_sentimento1, 3)
        }

    @staticmethod
    def generate_ai_analysis(campaign1, campaign2, evolution_data):
        """
        Gera uma análise textual da evolução entre campanhas.

        Esta análise pode ser expandida para usar GPT-4 via OpenRouter,
        mas por ora retorna uma análise baseada em regras.

        Args:
            campaign1: Campanha antiga
            campaign2: Campanha nova
            evolution_data: Dados de evolução calculados

        Returns:
            str com análise textual
        """
        summary = evolution_data['summary']
        dimensions = evolution_data['dimensions']
        sectors = evolution_data['sectors']

        # Determinar se houve melhora geral
        igrp_melhorou = summary['variacao']['igrp'] < 0
        risco_alto_diminuiu = summary['variacao']['pct_risco_alto'] < 0

        analysis_parts = []

        # Análise geral
        if igrp_melhorou and risco_alto_diminuiu:
            analysis_parts.append(
                f"A empresa apresentou melhora significativa nos indicadores de risco psicossocial. "
                f"O IGRP reduziu de {summary['campaign1']['igrp']} para {summary['campaign2']['igrp']}, "
                f"representando uma diminuição de {abs(summary['variacao']['igrp']):.1f} pontos."
            )
        elif igrp_melhorou:
            analysis_parts.append(
                f"A empresa apresentou melhora no IGRP, que reduziu de {summary['campaign1']['igrp']} "
                f"para {summary['campaign2']['igrp']}."
            )
        else:
            analysis_parts.append(
                f"Os indicadores mostram necessidade de atenção. O IGRP aumentou de "
                f"{summary['campaign1']['igrp']} para {summary['campaign2']['igrp']}."
            )

        # Análise de dimensões
        dimensoes_melhoraram = [d for d in dimensions if d['tendencia'] == 'melhora']
        if dimensoes_melhoraram:
            top_dimensao = max(dimensoes_melhoraram, key=lambda x: abs(x['variacao']))
            analysis_parts.append(
                f"A dimensão '{top_dimensao['dimensao']}' apresentou a maior melhora, "
                f"com variação de {top_dimensao['variacao']:+.2f} pontos."
            )

        # Análise de setores
        if sectors['melhoraram']:
            top_setor = sectors['melhoraram'][0]
            analysis_parts.append(
                f"As ações implementadas no setor de {top_setor['setor']} geraram impacto positivo, "
                f"com redução do IGRP de {abs(top_setor['variacao']):.1f} pontos "
                f"({top_setor['igrp_c1']} → {top_setor['igrp_c2']})."
            )

        if sectors['pioraram']:
            analysis_parts.append(
                f"Recomenda-se atenção aos setores que apresentaram piora, "
                f"especialmente '{sectors['pioraram'][0]['setor']}'."
            )

        return " ".join(analysis_parts)
