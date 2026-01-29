from django.db.models import Avg, Count
from apps.responses.models import SurveyResponse
from services.score_service import ScoreService


class RiskService:
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
