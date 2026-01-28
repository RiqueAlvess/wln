from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from apps.invitations.models import SurveyInvitation
from apps.responses.models import SurveyResponse
from apps.surveys.models import Pergunta
from services.token_service import TokenService
from services.notification_service import NotificationService


class SurveyFormView(View):
    @method_decorator(ratelimit(key='ip', rate='30/h', method='POST', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, token):
        invitation = get_object_or_404(SurveyInvitation, hash_token=token)
        valid, error_msg = TokenService.validate_token(invitation)

        if not valid:
            return render(request, 'survey/error.html', {'message': error_msg})

        step = request.GET.get('step', 'lgpd')

        if step == 'lgpd':
            return render(request, 'survey/step_lgpd.html', {
                'campaign': invitation.campaign,
                'empresa': invitation.empresa
            })

        elif step == 'demographics':
            return render(request, 'survey/step_demographics.html', {
                'campaign': invitation.campaign,
                'unidade': invitation.unidade,
                'setor': invitation.setor,
                'cargo': invitation.cargo
            })

        else:
            perguntas = Pergunta.objects.filter(ativo=True).order_by('numero')
            current_question = int(step) if step.isdigit() else 1

            if current_question > perguntas.count():
                return render(request, 'survey/step_success.html')

            pergunta = perguntas[current_question - 1]
            return render(request, 'survey/step_question.html', {
                'pergunta': pergunta,
                'current': current_question,
                'total': perguntas.count(),
                'dimensao': pergunta.dimensao,
                'escala': [(0, 'Nunca'), (1, 'Raramente'), (2, 'Às vezes'), (3, 'Frequentemente'), (4, 'Sempre')]
            })

    def post(self, request, token):
        invitation = get_object_or_404(SurveyInvitation, hash_token=token)
        valid, error_msg = TokenService.validate_token(invitation)

        if not valid:
            return render(request, 'survey/error.html', {'message': error_msg})

        step = request.POST.get('step', 'lgpd')

        if step == 'lgpd':
            if request.POST.get('lgpd_aceito') == 'on':
                return redirect(f'/survey/{token}/?step=demographics')

        elif step == 'demographics':
            request.session[f'survey_{token}'] = {
                'faixa_etaria': request.POST.get('faixa_etaria'),
                'tempo_empresa': request.POST.get('tempo_empresa'),
                'genero': request.POST.get('genero')
            }
            return redirect(f'/survey/{token}/?step=1')

        elif step.isdigit():
            current = int(step)
            if f'respostas_{token}' not in request.session:
                request.session[f'respostas_{token}'] = {}

            request.session[f'respostas_{token}'][step] = request.POST.get('valor')
            request.session.modified = True

            perguntas = Pergunta.objects.filter(ativo=True).count()
            if current >= perguntas:
                demographics = request.session.get(f'survey_{token}', {})
                respostas = request.session.get(f'respostas_{token}', {})

                survey_response = SurveyResponse.objects.create(
                    campaign=invitation.campaign,
                    unidade=invitation.unidade,
                    setor=invitation.setor,
                    cargo=invitation.cargo,
                    faixa_etaria=demographics['faixa_etaria'],
                    tempo_empresa=demographics['tempo_empresa'],
                    genero=demographics['genero'],
                    respostas=respostas,
                    lgpd_aceito=True,
                    lgpd_aceito_em=timezone.now()
                )

                # Enviar notificações após salvar resposta
                NotificationService.enviar_resultado_individual(survey_response)
                NotificationService.alerta_risco_critico(survey_response)

                TokenService.invalidate_token(invitation)

                del request.session[f'survey_{token}']
                del request.session[f'respostas_{token}']

                return render(request, 'survey/step_success.html')

            return redirect(f'/survey/{token}/?step={current + 1}')

        return redirect(f'/survey/{token}/')
