from django.db.models import Avg, Count
from apps.responses.models import SurveyResponse
from services.score_service import ScoreService


# Classificação de Riscos conforme NR-1
CLASSIFICACAO_RISCOS = {
    'critico': {
        'nome': 'CRÍTICO',
        'nome_nr1': 'Risco Intolerável',
        'cor_hex': '#dc3545',
        'cor_nome': 'Vermelho',
        'acao': 'Intervenção IMEDIATA obrigatória',
        'prazo_max': '30 dias',
        'icone': '🔴',
        'badge_class': 'bg-danger'
    },
    'importante': {
        'nome': 'IMPORTANTE',
        'nome_nr1': 'Risco Substancial',
        'cor_hex': '#fd7e14',
        'cor_nome': 'Laranja',
        'acao': 'Ação prioritária necessária',
        'prazo_max': '60 dias',
        'icone': '🟠',
        'badge_class': 'bg-warning text-dark'
    },
    'moderado': {
        'nome': 'MODERADO',
        'nome_nr1': 'Risco Tolerável com Controle',
        'cor_hex': '#ffc107',
        'cor_nome': 'Amarelo',
        'acao': 'Monitoramento e ações preventivas',
        'prazo_max': '90 dias',
        'icone': '🟡',
        'badge_class': 'bg-warning'
    },
    'aceitavel': {
        'nome': 'ACEITÁVEL',
        'nome_nr1': 'Risco Trivial',
        'cor_hex': '#28a745',
        'cor_nome': 'Verde',
        'acao': 'Manter controles existentes',
        'prazo_max': 'Revisão anual',
        'icone': '🟢',
        'badge_class': 'bg-success'
    }
}


class RiskService:
    @staticmethod
    def get_classificacao_por_nivel(nivel_risco: int) -> str:
        """
        Retorna a classificação baseada no nível de risco (1-16).

        Args:
            nivel_risco: Nível de risco calculado (probabilidade × severidade)

        Returns:
            Chave da classificação: 'critico', 'importante', 'moderado', 'aceitavel'
        """
        if nivel_risco >= 13:
            return 'critico'
        elif nivel_risco >= 9:
            return 'importante'
        elif nivel_risco >= 5:
            return 'moderado'
        else:
            return 'aceitavel'

    @staticmethod
    def get_info_classificacao(nivel_risco: int) -> dict:
        """
        Retorna informações completas da classificação NR-1 para um nível de risco.

        Args:
            nivel_risco: Nível de risco calculado (1-16)

        Returns:
            Dicionário com informações completas da classificação
        """
        chave = RiskService.get_classificacao_por_nivel(nivel_risco)
        return CLASSIFICACAO_RISCOS[chave]

    @staticmethod
    def _apply_filters(queryset, filters=None):
        """
        Aplica filtros de unidade e setor ao queryset.
        """
        if not filters:
            return queryset

        if filters.get('unidade_id'):
            queryset = queryset.filter(unidade_id=filters['unidade_id'])

        if filters.get('setor_id'):
            queryset = queryset.filter(setor_id=filters['setor_id'])

        return queryset

    @staticmethod
    def calcular_igrp(campaign, filters=None):
        responses_qs = SurveyResponse.objects.filter(campaign=campaign)
        responses_qs = RiskService._apply_filters(responses_qs, filters)
        responses = responses_qs

        if not responses.exists():
            return 0.0

        total_score = 0
        total_dimensoes = 0

        for response in responses:
            scores = ScoreService.processar_resposta_completa(response.respostas)
            for dimensao, data in scores.items():
                total_score += data['nivel']
                total_dimensoes += 1

        if total_dimensoes == 0:
            return 0.0

        return round(total_score / total_dimensoes, 2)

    @staticmethod
    def get_distribuicao_riscos(campaign, filters=None):
        responses_qs = SurveyResponse.objects.filter(campaign=campaign)
        responses_qs = RiskService._apply_filters(responses_qs, filters)
        responses = responses_qs

        critico = 0
        importante = 0
        moderado = 0
        aceitavel = 0

        for response in responses:
            scores = ScoreService.processar_resposta_completa(response.respostas)
            for dimensao, data in scores.items():
                nr = data['nivel']
                if nr >= 13:
                    critico += 1
                elif nr >= 9:
                    importante += 1
                elif nr >= 5:
                    moderado += 1
                else:
                    aceitavel += 1

        total = critico + importante + moderado + aceitavel
        return {
            'critico': critico,
            'importante': importante,
            'moderado': moderado,
            'aceitavel': aceitavel,
            'total': total,
            'percentual_alto': round((critico + importante) / total * 100, 2) if total > 0 else 0
        }
