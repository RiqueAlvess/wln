from django.db.models import Count, Avg
from apps.responses.models import SurveyResponse
from apps.invitations.models import SurveyInvitation
from services.score_service import ScoreService
from collections import defaultdict


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

    @staticmethod
    def get_demografico_genero(campaign):
        responses = SurveyResponse.objects.filter(campaign=campaign)
        genero_map = {'M': 'Masculino', 'F': 'Feminino', 'O': 'Outro', 'N': 'Não informado'}

        genero_count = defaultdict(int)
        for response in responses:
            genero = genero_map.get(response.genero, 'Não informado')
            genero_count[genero] += 1

        labels = list(genero_count.keys())
        values = list(genero_count.values())

        return {'labels': labels, 'values': values}

    @staticmethod
    def get_demografico_faixa_etaria(campaign):
        responses = SurveyResponse.objects.filter(campaign=campaign)

        faixa_count = defaultdict(int)
        for response in responses:
            faixa_count[response.faixa_etaria] += 1

        faixas_ordem = ['18-24', '25-34', '35-49', '50-59', '60+']
        labels = [f for f in faixas_ordem if f in faixa_count]
        values = [faixa_count[f] for f in labels]

        return {'labels': labels, 'values': values}

    @staticmethod
    def get_heatmap_data(campaign):
        responses = SurveyResponse.objects.filter(campaign=campaign).select_related('setor')

        setor_dimensoes = defaultdict(lambda: defaultdict(list))

        for response in responses:
            setor_nome = response.setor.nome
            for dimensao in ScoreService.DIMENSOES.keys():
                score = ScoreService.calcular_score_dimensao(response.respostas, dimensao)
                setor_dimensoes[setor_nome][dimensao].append(score)

        heatmap_data = []
        for setor, dimensoes_scores in setor_dimensoes.items():
            scores = []
            for dimensao in ScoreService.DIMENSOES.keys():
                if dimensoes_scores[dimensao]:
                    avg_score = round(sum(dimensoes_scores[dimensao]) / len(dimensoes_scores[dimensao]), 2)
                else:
                    avg_score = 0.0
                scores.append(avg_score)

            heatmap_data.append({'setor': setor, 'scores': scores})

        heatmap_data.sort(key=lambda x: sum(x['scores']), reverse=False)
        return heatmap_data[:10]

    @staticmethod
    def get_scores_por_genero(campaign):
        """
        Retorna dict com {genero: {dimensao: score_medio}}
        """
        responses = SurveyResponse.objects.filter(campaign=campaign)
        genero_map = {'M': 'Masculino', 'F': 'Feminino', 'O': 'Outro', 'N': 'Não informado'}

        genero_dimensoes = defaultdict(lambda: defaultdict(list))

        for response in responses:
            genero = genero_map.get(response.genero, 'Não informado')
            for dimensao in ScoreService.DIMENSOES.keys():
                score = ScoreService.calcular_score_dimensao(response.respostas, dimensao)
                genero_dimensoes[genero][dimensao].append(score)

        result = {}
        for genero, dimensoes_scores in genero_dimensoes.items():
            result[genero] = {}
            for dimensao in ScoreService.DIMENSOES.keys():
                if dimensoes_scores[dimensao]:
                    avg_score = round(sum(dimensoes_scores[dimensao]) / len(dimensoes_scores[dimensao]), 2)
                else:
                    avg_score = 0.0
                result[genero][dimensao] = avg_score

        return result

    @staticmethod
    def get_scores_por_faixa_etaria(campaign):
        """
        Retorna dict com {faixa: {dimensao: score_medio}}
        """
        responses = SurveyResponse.objects.filter(campaign=campaign)

        faixa_dimensoes = defaultdict(lambda: defaultdict(list))

        for response in responses:
            faixa = response.faixa_etaria
            for dimensao in ScoreService.DIMENSOES.keys():
                score = ScoreService.calcular_score_dimensao(response.respostas, dimensao)
                faixa_dimensoes[faixa][dimensao].append(score)

        result = {}
        for faixa, dimensoes_scores in faixa_dimensoes.items():
            result[faixa] = {}
            for dimensao in ScoreService.DIMENSOES.keys():
                if dimensoes_scores[dimensao]:
                    avg_score = round(sum(dimensoes_scores[dimensao]) / len(dimensoes_scores[dimensao]), 2)
                else:
                    avg_score = 0.0
                result[faixa][dimensao] = avg_score

        return result

    @staticmethod
    def get_top_grupos_demograficos_criticos(campaign, limit=3):
        """
        Retorna TOP N grupos demográficos com maior percentual de respostas em risco crítico.
        Grupos incluem combinações de gênero e faixa etária.
        """
        responses = SurveyResponse.objects.filter(campaign=campaign)
        genero_map = {'M': 'Masculino', 'F': 'Feminino', 'O': 'Outro', 'N': 'Não informado'}

        grupos_riscos = defaultdict(lambda: {'total': 0, 'criticos': 0})

        for response in responses:
            genero = genero_map.get(response.genero, 'Não informado')
            faixa = response.faixa_etaria
            grupo = f"{genero} ({faixa})"

            scores = ScoreService.processar_resposta_completa(response.respostas)

            for dimensao, data in scores.items():
                grupos_riscos[grupo]['total'] += 1
                if data['nivel'] >= 13:
                    grupos_riscos[grupo]['criticos'] += 1

        top_grupos = []
        for grupo, data in grupos_riscos.items():
            if data['total'] > 0:
                pct_critico = (data['criticos'] / data['total'] * 100)
                top_grupos.append({
                    'grupo': grupo,
                    'nivel_risco': round(pct_critico, 1),
                    'total_respostas': data['total'] // len(ScoreService.DIMENSOES),
                    'cor': 'vermelho' if pct_critico > 50 else 'laranja' if pct_critico > 25 else 'amarelo'
                })

        top_grupos.sort(key=lambda x: x['nivel_risco'], reverse=True)
        return top_grupos[:limit]
