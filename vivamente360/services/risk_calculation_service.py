"""
Serviço de Cálculo de Risco Psicossocial (100% Determinístico)

Implementa a matriz de risco conforme NR-1:
- NR (Nível de Risco) = P (Probabilidade) × S (Severidade)
- Probabilidade baseada nos scores HSE-IT
- Severidade baseada nos fatores de risco e CNAE da empresa
"""

from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from apps.surveys.models import (
    FatorRisco,
    SeveridadePorCNAE,
    Dimensao
)
from app_selectors.dashboard_selectors import DashboardSelectors


class RiskCalculationService:
    """
    Serviço de cálculo de risco 100% determinístico (sem IA).
    Implementa a fórmula NR = P × S conforme NR-1.
    """

    # ============================================================================
    # MAPEAMENTO SCORE HSE-IT → PROBABILIDADE
    # ============================================================================

    # Mapeamento Score HSE-IT (0-4) → Probabilidade (1-5)
    PROBABILIDADE_MAP = {
        'negativo': {  # Dimensões onde score ALTO = RISCO ALTO
            (3.5, 4.0): 5,  # Quase Certo
            (2.5, 3.5): 4,  # Provável
            (1.5, 2.5): 3,  # Possível
            (0.5, 1.5): 2,  # Improvável
            (0.0, 0.5): 1,  # Raro
        },
        'positivo': {  # Dimensões onde score BAIXO = RISCO ALTO
            (0.0, 0.5): 5,  # Quase Certo
            (0.5, 1.5): 4,  # Provável
            (1.5, 2.5): 3,  # Possível
            (2.5, 3.5): 2,  # Improvável
            (3.5, 4.0): 1,  # Raro
        }
    }

    PROBABILIDADE_LABELS = {
        1: {
            'nome': 'Raro',
            'descricao': 'Pode ocorrer apenas em circunstâncias excepcionais',
            'cor': '#28a745',
            'icone': '🟢'
        },
        2: {
            'nome': 'Improvável',
            'descricao': 'Não é esperado que ocorra',
            'cor': '#20c997',
            'icone': '🟢'
        },
        3: {
            'nome': 'Possível',
            'descricao': 'Pode ocorrer em algum momento',
            'cor': '#ffc107',
            'icone': '🟡'
        },
        4: {
            'nome': 'Provável',
            'descricao': 'Provavelmente ocorrerá na maioria das circunstâncias',
            'cor': '#fd7e14',
            'icone': '🟠'
        },
        5: {
            'nome': 'Quase Certo',
            'descricao': 'Espera-se que ocorra na maioria das circunstâncias',
            'cor': '#dc3545',
            'icone': '🔴'
        },
    }

    # ============================================================================
    # SEVERIDADE
    # ============================================================================

    SEVERIDADE_LABELS = {
        1: {
            'nome': 'Insignificante',
            'descricao': 'Sem lesão ou doença / Desconforto temporário',
            'exemplos': 'Fadiga leve, irritação passageira',
            'cor': '#28a745',
            'icone': '🟢'
        },
        2: {
            'nome': 'Menor',
            'descricao': 'Lesão leve / Doença leve sem afastamento',
            'exemplos': 'Dor de cabeça, estresse pontual, insônia ocasional',
            'cor': '#ffc107',
            'icone': '🟡'
        },
        3: {
            'nome': 'Moderada',
            'descricao': 'Lesão moderada / Doença com afastamento temporário',
            'exemplos': 'Ansiedade persistente, distúrbios de sono, início de burnout',
            'cor': '#fd7e14',
            'icone': '🟠'
        },
        4: {
            'nome': 'Significativa',
            'descricao': 'Lesão grave / Doença com afastamento prolongado',
            'exemplos': 'Depressão, síndrome de burnout, DORT, doenças cardiovasculares',
            'cor': '#dc3545',
            'icone': '🔴'
        },
        5: {
            'nome': 'Catastrófica',
            'descricao': 'Incapacidade permanente / Óbito',
            'exemplos': 'Suicídio, infarto, AVC, incapacidade total para o trabalho',
            'cor': '#6f42c1',
            'icone': '🟣'
        },
    }

    # ============================================================================
    # MATRIZ DE RISCO 5x5 (P × S)
    # ============================================================================

    # Valores possíveis: 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 20, 25
    MATRIZ_RISCO = {
        (1, 1): 1,  (1, 2): 2,  (1, 3): 3,  (1, 4): 4,  (1, 5): 5,
        (2, 1): 2,  (2, 2): 4,  (2, 3): 6,  (2, 4): 8,  (2, 5): 10,
        (3, 1): 3,  (3, 2): 6,  (3, 3): 9,  (3, 4): 12, (3, 5): 15,
        (4, 1): 4,  (4, 2): 8,  (4, 3): 12, (4, 4): 16, (4, 5): 20,
        (5, 1): 5,  (5, 2): 10, (5, 3): 15, (5, 4): 20, (5, 5): 25,
    }

    # ============================================================================
    # CLASSIFICAÇÃO DO NÍVEL DE RISCO
    # ============================================================================

    CLASSIFICACAO_NR = {
        (1, 4): {
            'classificacao': 'TRIVIAL',
            'cor': '#28a745',
            'cor_nome': 'Verde',
            'acao': 'Manter controles existentes. Nenhuma ação adicional necessária.',
            'prazo': None,
            'prioridade': 4,
            'icone': '🟢',
            'badge_class': 'bg-success'
        },
        (5, 9): {
            'classificacao': 'TOLERÁVEL',
            'cor': '#ffc107',
            'cor_nome': 'Amarelo',
            'acao': 'Monitorar. Considerar melhorias que não impliquem custos significativos.',
            'prazo': '180 dias',
            'prioridade': 3,
            'icone': '🟡',
            'badge_class': 'bg-warning'
        },
        (10, 14): {
            'classificacao': 'MODERADO',
            'cor': '#fd7e14',
            'cor_nome': 'Laranja',
            'acao': 'Ação necessária dentro do prazo determinado. Implementar controles.',
            'prazo': '90 dias',
            'prioridade': 2,
            'icone': '🟠',
            'badge_class': 'bg-orange'
        },
        (15, 19): {
            'classificacao': 'SUBSTANCIAL',
            'cor': '#dc3545',
            'cor_nome': 'Vermelho',
            'acao': 'Ação urgente. O trabalho não deve continuar até que o risco seja reduzido.',
            'prazo': '30 dias',
            'prioridade': 1,
            'icone': '🔴',
            'badge_class': 'bg-danger'
        },
        (20, 25): {
            'classificacao': 'INTOLERÁVEL',
            'cor': '#6f42c1',
            'cor_nome': 'Roxo',
            'acao': 'INTERVENÇÃO IMEDIATA. Trabalho deve ser interrompido até implementação de controles.',
            'prazo': 'Imediato',
            'prioridade': 0,
            'icone': '🟣',
            'badge_class': 'bg-purple'
        },
    }

    # ============================================================================
    # MÉTODOS PRINCIPAIS
    # ============================================================================

    @classmethod
    def calcular_probabilidade(cls, score: float, tipo_dimensao: str) -> int:
        """
        Converte score HSE-IT (0-4) em Probabilidade (1-5).

        Args:
            score: Score médio da dimensão (0.0 a 4.0)
            tipo_dimensao: 'negativo' ou 'positivo'

        Returns:
            Probabilidade de 1 a 5
        """
        mapa = cls.PROBABILIDADE_MAP.get(tipo_dimensao, cls.PROBABILIDADE_MAP['positivo'])

        for (min_score, max_score), probabilidade in mapa.items():
            if min_score <= score <= max_score:
                return probabilidade

        # Default: Possível
        return 3

    @classmethod
    def obter_severidade(
        cls,
        fator_risco: FatorRisco,
        cnae: Optional[str] = None
    ) -> int:
        """
        Obtém severidade do fator de risco, ajustada por CNAE se disponível.

        Args:
            fator_risco: Objeto FatorRisco
            cnae: Código CNAE da empresa (opcional, ex: "62.01-5")

        Returns:
            Severidade de 1 a 5
        """
        severidade = fator_risco.severidade_base

        if cnae and len(cnae) > 0:
            # Extrair seção (primeira letra/número) e divisão se houver
            cnae_limpo = cnae.replace('.', '').replace('-', '')
            secao = cnae_limpo[0] if cnae_limpo else None
            divisao = cnae_limpo[0:2] if len(cnae_limpo) >= 2 else None

            # Verificar se há ajuste específico para este CNAE
            if secao:
                # Tentar buscar ajuste mais específico (seção + divisão)
                if divisao:
                    ajuste = SeveridadePorCNAE.objects.filter(
                        fator_risco=fator_risco,
                        cnae_secao=secao,
                        cnae_divisao=divisao
                    ).first()
                    if ajuste:
                        return ajuste.severidade_ajustada

                # Se não encontrou específico, buscar apenas por seção
                ajuste = SeveridadePorCNAE.objects.filter(
                    fator_risco=fator_risco,
                    cnae_secao=secao,
                    cnae_divisao=''
                ).first()
                if ajuste:
                    severidade = ajuste.severidade_ajustada

        return severidade

    @classmethod
    def calcular_nivel_risco(
        cls,
        probabilidade: int,
        severidade: int
    ) -> Dict:
        """
        Calcula o Nível de Risco (NR = P × S) e retorna classificação completa.

        Args:
            probabilidade: 1 a 5
            severidade: 1 a 5

        Returns:
            Dict com NR, classificação, cor, ação e prazo
        """
        nr = probabilidade * severidade

        # Encontrar classificação
        for (min_nr, max_nr), classificacao in cls.CLASSIFICACAO_NR.items():
            if min_nr <= nr <= max_nr:
                return {
                    'nr': nr,
                    'probabilidade': probabilidade,
                    'probabilidade_label': cls.PROBABILIDADE_LABELS[probabilidade],
                    'severidade': severidade,
                    'severidade_label': cls.SEVERIDADE_LABELS[severidade],
                    **classificacao
                }

        # Fallback (não deveria acontecer)
        return {
            'nr': nr,
            'probabilidade': probabilidade,
            'severidade': severidade,
            'classificacao': 'INDEFINIDO'
        }

    @classmethod
    def processar_dimensao_completa(
        cls,
        dimensao: Dimensao,
        score: float,
        cnae: Optional[str] = None
    ) -> List[Dict]:
        """
        Processa uma dimensão HSE-IT e retorna todos os fatores de risco associados.

        Args:
            dimensao: Objeto Dimensao HSE-IT
            score: Score médio da dimensão (0.0 a 4.0)
            cnae: CNAE da empresa

        Returns:
            Lista de dicts com análise de cada fator de risco
        """
        fatores_associados = dimensao.fatores_risco.filter(ativo=True)
        resultados = []

        for fator in fatores_associados:
            probabilidade = cls.calcular_probabilidade(score, dimensao.tipo)
            severidade = cls.obter_severidade(fator, cnae)
            analise = cls.calcular_nivel_risco(probabilidade, severidade)

            resultados.append({
                'fator': fator,
                'dimensao': dimensao,
                'score_dimensao': score,
                **analise
            })

        return resultados

    @classmethod
    def gerar_matriz_completa(cls, campaign, cnae: Optional[str] = None) -> Dict:
        """
        Gera matriz de risco completa para uma campanha.

        Args:
            campaign: Objeto Campaign
            cnae: CNAE da empresa (pega da empresa se não fornecido)

        Returns:
            Dict com análise completa por dimensão e fator
        """
        # Usar CNAE da empresa se não fornecido
        if not cnae:
            cnae = getattr(campaign.empresa, 'cnae', None)

        # Obter scores das dimensões
        scores = DashboardSelectors.get_dimensoes_scores(campaign)
        dimensoes = Dimensao.objects.filter(ativo=True)

        resultado = {
            'campaign': campaign,
            'cnae': cnae,
            'data_analise': timezone.now(),
            'dimensoes': [],
            'fatores_criticos': [],
            'resumo': {
                'total_fatores': 0,
                'intoleraveis': 0,
                'substanciais': 0,
                'moderados': 0,
                'toleraveis': 0,
                'triviais': 0,
            }
        }

        for dimensao in dimensoes:
            score = scores.get(dimensao.codigo, 2.0)  # Default: 2.0 (neutro)
            fatores_analisados = cls.processar_dimensao_completa(dimensao, score, cnae)

            dimensao_resultado = {
                'dimensao': dimensao,
                'score': score,
                'fatores': fatores_analisados,
            }
            resultado['dimensoes'].append(dimensao_resultado)

            # Contabilizar resumo
            for fator in fatores_analisados:
                resultado['resumo']['total_fatores'] += 1

                classificacao = fator.get('classificacao', 'TRIVIAL')
                if classificacao == 'INTOLERÁVEL':
                    resultado['resumo']['intoleraveis'] += 1
                    resultado['fatores_criticos'].append(fator)
                elif classificacao == 'SUBSTANCIAL':
                    resultado['resumo']['substanciais'] += 1
                    resultado['fatores_criticos'].append(fator)
                elif classificacao == 'MODERADO':
                    resultado['resumo']['moderados'] += 1
                elif classificacao == 'TOLERÁVEL':
                    resultado['resumo']['toleraveis'] += 1
                else:  # TRIVIAL
                    resultado['resumo']['triviais'] += 1

        # Ordenar fatores críticos por prioridade e NR
        resultado['fatores_criticos'].sort(
            key=lambda x: (x.get('prioridade', 99), -x.get('nr', 0))
        )

        return resultado

    @classmethod
    def gerar_matriz_visual(cls, fatores_analisados: List[Dict]) -> Dict:
        """
        Gera dados para visualização da matriz 5×5.

        Args:
            fatores_analisados: Lista de fatores já processados

        Returns:
            Dict com estrutura da matriz para visualização
        """
        # Inicializar matriz 5x5 vazia
        matriz = {}
        for p in range(1, 6):
            for s in range(1, 6):
                matriz[(p, s)] = {
                    'count': 0,
                    'fatores': [],
                    'nr': p * s
                }

        # Preencher matriz com fatores
        for fator_data in fatores_analisados:
            p = fator_data.get('probabilidade', 1)
            s = fator_data.get('severidade', 1)
            matriz[(p, s)]['count'] += 1
            matriz[(p, s)]['fatores'].append(fator_data)

        return {
            'matriz': matriz,
            'total_fatores': len(fatores_analisados)
        }
