"""
Serviço de Avaliação Completa de Risco Psicossocial (Algoritmo + IA)

Combina:
1. Cálculo algorítmico (NR = P × S) via RiskCalculationService
2. Análise de comentários via IA (AICommentAnalysisService)
3. Ajuste de probabilidades baseado em evidências qualitativas
"""

from typing import Dict, List, Optional
from django.utils import timezone
from apps.structure.models import Setor
from services.risk_calculation_service import RiskCalculationService
from services.ai_comment_analysis_service import AICommentAnalysisService
from app_selectors.dashboard_selectors import DashboardSelectors


class RiskAssessmentService:
    """
    Serviço completo de avaliação de risco que combina:
    - Cálculo algorítmico (NR = P × S)
    - Análise de IA (comentários)
    """

    @classmethod
    def avaliar_campanha_completa(
        cls,
        campaign,
        processar_ia: bool = True,
        setores_ids: Optional[List[int]] = None
    ) -> Dict:
        """
        Executa avaliação completa de uma campanha.

        Processo:
        1. Calcula scores HSE-IT (algoritmo)
        2. Gera matriz P×S base (algoritmo)
        3. Coleta comentários por setor
        4. Analisa comentários com IA (se houver e se processar_ia=True)
        5. Ajusta probabilidades baseado na IA
        6. Gera matriz final combinada

        Args:
            campaign: Objeto Campaign
            processar_ia: Se True, processa análise de IA (default: True)
            setores_ids: Lista de IDs de setores para processar (None = todos)

        Returns:
            Dict com avaliação completa
        """
        empresa = campaign.empresa
        cnae = getattr(empresa, 'cnae', None)

        # ETAPA 1: Cálculo algorítmico base
        matriz_base = RiskCalculationService.gerar_matriz_completa(campaign, cnae)

        # ETAPA 2: Preparar para análise de IA
        analises_ia = {}
        ajustes_por_fator = {}

        if processar_ia:
            # Determinar setores a processar
            if setores_ids:
                setores = Setor.objects.filter(
                    id__in=setores_ids,
                    unidade__empresa=empresa
                )
            else:
                setores = Setor.objects.filter(
                    unidade__empresa=empresa
                ).distinct()

            ai_service = AICommentAnalysisService()

            for setor in setores:
                # ETAPA 3: Análise IA por setor
                analise = ai_service.analisar_comentarios_setor(campaign, setor)

                if 'erro' not in analise:
                    analises_ia[setor.id] = analise

                    # ETAPA 4: Extrair ajustes de probabilidade
                    for fator_ia in analise.get('fatores_identificados', []):
                        codigo = fator_ia.get('codigo_fator')
                        ajuste = fator_ia.get('ajuste_probabilidade', 0)

                        if codigo:
                            if codigo not in ajustes_por_fator:
                                ajustes_por_fator[codigo] = []
                            ajustes_por_fator[codigo].append({
                                'ajuste': ajuste,
                                'setor_id': setor.id,
                                'justificativa': fator_ia.get('justificativa_ajuste', '')
                            })

        # ETAPA 5: Aplicar ajustes da IA na matriz
        matriz_ajustada = cls._aplicar_ajustes_ia(
            matriz_base.copy(),
            ajustes_por_fator
        ) if ajustes_por_fator else matriz_base

        # ETAPA 6: Extrair alertas críticos
        alertas_criticos = []
        if analises_ia:
            ai_service = AICommentAnalysisService()
            alertas_criticos = ai_service.extrair_alertas_criticos(analises_ia)

        # ETAPA 7: Compilar resultado final
        return {
            'campaign': campaign,
            'empresa': empresa,
            'cnae': cnae,
            'data_avaliacao': timezone.now(),
            'matriz_base': matriz_base,
            'matriz_ajustada': matriz_ajustada,
            'analises_ia': analises_ia,
            'alertas_criticos': alertas_criticos,
            'resumo': cls._gerar_resumo(matriz_ajustada, analises_ia),
            'processou_ia': processar_ia and len(analises_ia) > 0,
        }

    @classmethod
    def avaliar_setor_especifico(
        cls,
        campaign,
        setor: Setor,
        processar_ia: bool = True
    ) -> Dict:
        """
        Avalia riscos de um setor específico.

        Args:
            campaign: Objeto Campaign
            setor: Objeto Setor
            processar_ia: Se True, processa análise de IA

        Returns:
            Dict com avaliação do setor
        """
        empresa = campaign.empresa
        cnae = getattr(empresa, 'cnae', None)

        # Calcular scores apenas do setor
        from apps.surveys.models import Dimensao
        from apps.responses.models import SurveyResponse
        from services.score_service import ScoreService

        dimensoes = Dimensao.objects.filter(ativo=True)
        respostas_setor = SurveyResponse.objects.filter(
            campaign=campaign,
            setor=setor
        )

        scores_dimensoes = {}
        for dimensao in dimensoes:
            scores_lista = []
            for resposta in respostas_setor:
                score = ScoreService.calcular_score_dimensao(
                    resposta.respostas,
                    dimensao.codigo
                )
                if score is not None:
                    scores_lista.append(score)

            if scores_lista:
                scores_dimensoes[dimensao.codigo] = sum(scores_lista) / len(scores_lista)

        # Processar fatores por dimensão
        fatores_analisados = []
        for dimensao in dimensoes:
            score = scores_dimensoes.get(dimensao.codigo, 2.0)
            fatores = RiskCalculationService.processar_dimensao_completa(
                dimensao, score, cnae
            )
            fatores_analisados.extend(fatores)

        # Análise de IA
        analise_ia = None
        if processar_ia:
            ai_service = AICommentAnalysisService()
            analise_ia = ai_service.analisar_comentarios_setor(campaign, setor)

            # Aplicar ajustes de IA
            if 'erro' not in analise_ia:
                for fator_data in fatores_analisados:
                    fator_obj = fator_data.get('fator')
                    if not fator_obj:
                        continue

                    # Buscar ajuste para este fator
                    for fator_ia in analise_ia.get('fatores_identificados', []):
                        if fator_ia.get('codigo_fator') == fator_obj.codigo:
                            prob_original = fator_data.get('probabilidade', 1)
                            ajuste = fator_ia.get('ajuste_probabilidade', 0)

                            if ajuste != 0:
                                ai_service_instance = AICommentAnalysisService()
                                prob_ajustada = ai_service_instance.ajustar_probabilidade_com_ia(
                                    prob_original, ajuste
                                )

                                # Recalcular NR com nova probabilidade
                                severidade = fator_data.get('severidade', 1)
                                novo_nr = RiskCalculationService.calcular_nivel_risco(
                                    prob_ajustada, severidade
                                )

                                # Atualizar dados do fator
                                fator_data['probabilidade_original'] = prob_original
                                fator_data['probabilidade'] = prob_ajustada
                                fator_data['ajuste_ia'] = ajuste
                                fator_data['ajuste_justificativa'] = fator_ia.get(
                                    'justificativa_ajuste', ''
                                )
                                fator_data.update(novo_nr)

        # Classificar fatores por nível de risco
        fatores_criticos = [
            f for f in fatores_analisados
            if f.get('classificacao') in ['INTOLERÁVEL', 'SUBSTANCIAL']
        ]
        fatores_criticos.sort(key=lambda x: (x.get('prioridade', 99), -x.get('nr', 0)))

        # Resumo
        resumo = {
            'total_fatores': len(fatores_analisados),
            'intoleraveis': sum(1 for f in fatores_analisados if f.get('classificacao') == 'INTOLERÁVEL'),
            'substanciais': sum(1 for f in fatores_analisados if f.get('classificacao') == 'SUBSTANCIAL'),
            'moderados': sum(1 for f in fatores_analisados if f.get('classificacao') == 'MODERADO'),
            'toleraveis': sum(1 for f in fatores_analisados if f.get('classificacao') == 'TOLERÁVEL'),
            'triviais': sum(1 for f in fatores_analisados if f.get('classificacao') == 'TRIVIAL'),
        }

        return {
            'campaign': campaign,
            'setor': setor,
            'cnae': cnae,
            'data_avaliacao': timezone.now(),
            'fatores': fatores_analisados,
            'fatores_criticos': fatores_criticos,
            'analise_ia': analise_ia,
            'resumo': resumo,
            'processou_ia': processar_ia and analise_ia and 'erro' not in analise_ia,
        }

    @classmethod
    def _aplicar_ajustes_ia(cls, matriz_base: Dict, ajustes: Dict) -> Dict:
        """
        Aplica ajustes da IA na matriz base.

        Args:
            matriz_base: Matriz calculada pelo algoritmo
            ajustes: Dict com {codigo_fator: [{'ajuste': int, 'setor_id': int, 'justificativa': str}]}

        Returns:
            Matriz com ajustes aplicados
        """
        matriz_ajustada = matriz_base.copy()

        for dimensao_data in matriz_ajustada.get('dimensoes', []):
            for fator in dimensao_data.get('fatores', []):
                fator_obj = fator.get('fator')
                if not fator_obj:
                    continue

                codigo = fator_obj.codigo

                if codigo in ajustes:
                    # Calcular ajuste médio (pode haver múltiplos setores)
                    ajustes_lista = [a['ajuste'] for a in ajustes[codigo]]
                    ajuste_medio = round(sum(ajustes_lista) / len(ajustes_lista))

                    # Aplicar ajuste
                    prob_original = fator.get('probabilidade', 1)
                    prob_ajustada = max(1, min(5, prob_original + ajuste_medio))

                    if prob_ajustada != prob_original:
                        # Recalcular NR
                        severidade = fator.get('severidade', 1)
                        novo_nr = RiskCalculationService.calcular_nivel_risco(
                            prob_ajustada,
                            severidade
                        )

                        # Coletar justificativas
                        justificativas = [
                            f"Setor {a['setor_id']}: {a.get('justificativa', 'N/A')}"
                            for a in ajustes[codigo]
                            if a.get('justificativa')
                        ]

                        fator.update({
                            'probabilidade_original': prob_original,
                            'probabilidade': prob_ajustada,
                            'ajuste_ia': ajuste_medio,
                            'ajuste_justificativas': justificativas,
                            **novo_nr
                        })

        # Recalcular resumo
        matriz_ajustada['resumo'] = {
            'total_fatores': 0,
            'intoleraveis': 0,
            'substanciais': 0,
            'moderados': 0,
            'toleraveis': 0,
            'triviais': 0,
        }

        fatores_criticos_novos = []

        for dimensao_data in matriz_ajustada.get('dimensoes', []):
            for fator in dimensao_data.get('fatores', []):
                matriz_ajustada['resumo']['total_fatores'] += 1

                classificacao = fator.get('classificacao', 'TRIVIAL')
                if classificacao == 'INTOLERÁVEL':
                    matriz_ajustada['resumo']['intoleraveis'] += 1
                    fatores_criticos_novos.append(fator)
                elif classificacao == 'SUBSTANCIAL':
                    matriz_ajustada['resumo']['substanciais'] += 1
                    fatores_criticos_novos.append(fator)
                elif classificacao == 'MODERADO':
                    matriz_ajustada['resumo']['moderados'] += 1
                elif classificacao == 'TOLERÁVEL':
                    matriz_ajustada['resumo']['toleraveis'] += 1
                else:
                    matriz_ajustada['resumo']['triviais'] += 1

        # Ordenar fatores críticos
        fatores_criticos_novos.sort(
            key=lambda x: (x.get('prioridade', 99), -x.get('nr', 0))
        )
        matriz_ajustada['fatores_criticos'] = fatores_criticos_novos

        return matriz_ajustada

    @classmethod
    def _gerar_resumo(cls, matriz: Dict, analises_ia: Dict) -> Dict:
        """
        Gera resumo executivo da avaliação.

        Args:
            matriz: Matriz de risco (base ou ajustada)
            analises_ia: Análises de IA por setor

        Returns:
            Dict com resumo consolidado
        """
        resumo = matriz.get('resumo', {}).copy()

        # Adicionar dados de sentimento se houver análises de IA
        if analises_ia:
            sentimentos = []
            niveis_preocupacao = {'Baixo': 0, 'Médio': 0, 'Alto': 0, 'Crítico': 0}

            for analise in analises_ia.values():
                resumo_geral = analise.get('resumo_geral', {})

                if 'score_sentimento' in resumo_geral:
                    sentimentos.append(resumo_geral['score_sentimento'])

                nivel = resumo_geral.get('nivel_preocupacao', 'Médio')
                if nivel in niveis_preocupacao:
                    niveis_preocupacao[nivel] += 1

            if sentimentos:
                sentimento_medio = sum(sentimentos) / len(sentimentos)
                resumo['sentimento_medio'] = sentimento_medio
                resumo['sentimento_label'] = (
                    'Positivo' if sentimento_medio > 0.3 else
                    'Negativo' if sentimento_medio < -0.3 else
                    'Neutro'
                )

            # Nível de preocupação predominante
            if niveis_preocupacao:
                nivel_predominante = max(
                    niveis_preocupacao.items(),
                    key=lambda x: x[1]
                )[0]
                resumo['nivel_preocupacao_predominante'] = nivel_predominante

            # Total de alertas críticos
            total_alertas = sum(
                len(a.get('alertas_criticos', []))
                for a in analises_ia.values()
            )
            resumo['alertas_criticos'] = total_alertas

        return resumo
