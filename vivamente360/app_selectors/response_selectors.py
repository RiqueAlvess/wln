from apps.responses.models import SurveyResponse
from django.db.models import Count


class ResponseSelectors:
    @staticmethod
    def get_campaign_responses(campaign):
        return SurveyResponse.objects.filter(campaign=campaign)

    @staticmethod
    def get_responses_by_setor(campaign, setor):
        return SurveyResponse.objects.filter(campaign=campaign, setor=setor)

    @staticmethod
    def get_responses_by_unidade(campaign, unidade):
        return SurveyResponse.objects.filter(campaign=campaign, unidade=unidade)

    @staticmethod
    def get_demographic_breakdown(campaign):
        responses = SurveyResponse.objects.filter(campaign=campaign)

        return {
            'faixa_etaria': responses.values('faixa_etaria').annotate(count=Count('id')),
            'tempo_empresa': responses.values('tempo_empresa').annotate(count=Count('id')),
            'genero': responses.values('genero').annotate(count=Count('id'))
        }
