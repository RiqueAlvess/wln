from django.db.models import Count, Avg
from apps.responses.models import SurveyResponse
from apps.invitations.models import SurveyInvitation
from services.score_service import ScoreService


class DashboardSelectors:
    @staticmethod
    def get_campaign_metrics(campaign):
        total_convidados = SurveyInvitation.objects.filter(campaign=campaign).count()
        total_respondidos = SurveyResponse.objects.filter(campaign=campaign).count()

        adesao = round((total_respondidos / total_convidados * 100), 2) if total_convidados > 0 else 0

        return {
            'total_convidados': total_convidados,
            'total_respondidos': total_respondidos,
            'adesao': adesao
        }

    @staticmethod
    def get_dimensoes_scores(campaign):
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
    def get_top_setores_criticos(campaign, limit=5):
        from django.db.models import Count
        from collections import defaultdict

        responses = SurveyResponse.objects.filter(campaign=campaign).select_related('setor')

        setor_riscos = defaultdict(lambda: {'total': 0, 'criticos': 0})

        for response in responses:
            setor_nome = response.setor.nome
            scores = ScoreService.processar_resposta_completa(response.respostas)

            for dimensao, data in scores.items():
                setor_riscos[setor_nome]['total'] += 1
                if data['nivel'] >= 13:
                    setor_riscos[setor_nome]['criticos'] += 1

        top_setores = []
        for setor, data in setor_riscos.items():
            pct_critico = (data['criticos'] / data['total'] * 100) if data['total'] > 0 else 0
            top_setores.append({
                'setor': setor,
                'nivel_risco': round(pct_critico, 1),
                'cor': 'vermelho' if pct_critico > 50 else 'laranja' if pct_critico > 25 else 'amarelo'
            })

        top_setores.sort(key=lambda x: x['nivel_risco'], reverse=True)
        return top_setores[:limit]
