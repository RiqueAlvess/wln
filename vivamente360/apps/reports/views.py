import logging
from django.views import View
from django.views.generic import TemplateView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from apps.core.mixins import RHRequiredMixin
from apps.tenants.models import Empresa
from .models import AnonymousReport, ReportResponse, ReportFollowUp

logger = logging.getLogger(__name__)


class ReportCreateView(View):
    """
    View pública para criar denúncia anônima.
    NÃO requer autenticação - qualquer pessoa com o link da empresa pode denunciar.
    Rate limited para prevenir abuso.
    """

    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, empresa_slug):
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return render(request, 'reports/create.html', {
            'empresa': empresa,
            'categorias': AnonymousReport.CATEGORIA_CHOICES,
            'gravidades': AnonymousReport.GRAVIDADE_CHOICES,
        })

    def post(self, request, empresa_slug):
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)

        categoria = request.POST.get('categoria', '').strip()
        gravidade = request.POST.get('gravidade', 'media').strip()
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        local_ocorrencia = request.POST.get('local_ocorrencia', '').strip()
        data_ocorrencia = request.POST.get('data_ocorrencia_aproximada', '').strip()

        # Validação
        errors = []
        if not categoria or categoria not in dict(AnonymousReport.CATEGORIA_CHOICES):
            errors.append('Categoria inválida.')
        if not titulo or len(titulo) < 10:
            errors.append('O título deve ter pelo menos 10 caracteres.')
        if not descricao or len(descricao) < 30:
            errors.append('A descrição deve ter pelo menos 30 caracteres.')
        if len(descricao) > 5000:
            errors.append('A descrição deve ter no máximo 5000 caracteres.')

        if errors:
            return render(request, 'reports/create.html', {
                'empresa': empresa,
                'categorias': AnonymousReport.CATEGORIA_CHOICES,
                'gravidades': AnonymousReport.GRAVIDADE_CHOICES,
                'errors': errors,
                'form_data': request.POST,
            })

        # Gerar token de acesso (entregue ao denunciante, NÃO armazenado em texto puro)
        access_token = AnonymousReport.generate_access_token()
        access_token_hash = AnonymousReport.hash_access_token(access_token)

        report = AnonymousReport.objects.create(
            empresa=empresa,
            categoria=categoria,
            gravidade=gravidade,
            titulo=titulo,
            descricao=descricao,
            local_ocorrencia=local_ocorrencia,
            data_ocorrencia_aproximada=data_ocorrencia,
            access_token_hash=access_token_hash,
        )

        return render(request, 'reports/success.html', {
            'empresa': empresa,
            'protocolo': report.protocolo,
            'access_token': access_token,
        })


class ReportTrackView(View):
    """
    View pública para acompanhar denúncia usando protocolo + token.
    NÃO requer autenticação.
    """

    @method_decorator(ratelimit(key='ip', rate='30/h', method=['GET', 'POST'], block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, empresa_slug):
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return render(request, 'reports/track.html', {'empresa': empresa})

    def post(self, request, empresa_slug):
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)

        protocolo = request.POST.get('protocolo', '').strip().upper()
        access_token = request.POST.get('access_token', '').strip()

        if not protocolo or not access_token:
            return render(request, 'reports/track.html', {
                'empresa': empresa,
                'error': 'Protocolo e chave de acesso são obrigatórios.',
            })

        # Validar protocolo e token
        access_token_hash = AnonymousReport.hash_access_token(access_token)

        try:
            report = AnonymousReport.objects.get(
                protocolo=protocolo,
                empresa=empresa,
                access_token_hash=access_token_hash,
            )
        except AnonymousReport.DoesNotExist:
            return render(request, 'reports/track.html', {
                'empresa': empresa,
                'error': 'Protocolo ou chave de acesso inválidos.',
            })

        # Buscar respostas visíveis ao denunciante
        respostas = report.respostas_rh.filter(visivel_denunciante=True)
        followups = report.followups.all()

        return render(request, 'reports/detail_anonymous.html', {
            'empresa': empresa,
            'report': report,
            'respostas': respostas,
            'followups': followups,
            'protocolo': protocolo,
            'access_token': access_token,
        })


class ReportFollowUpView(View):
    """
    View pública para o denunciante enviar informações adicionais.
    """

    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, empresa_slug):
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)

        protocolo = request.POST.get('protocolo', '').strip().upper()
        access_token = request.POST.get('access_token', '').strip()
        mensagem = request.POST.get('mensagem', '').strip()

        if not protocolo or not access_token or not mensagem:
            return JsonResponse({'error': 'Dados incompletos.'}, status=400)

        if len(mensagem) > 3000:
            return JsonResponse({'error': 'Mensagem muito longa (máximo 3000 caracteres).'}, status=400)

        access_token_hash = AnonymousReport.hash_access_token(access_token)

        try:
            report = AnonymousReport.objects.get(
                protocolo=protocolo,
                empresa=empresa,
                access_token_hash=access_token_hash,
            )
        except AnonymousReport.DoesNotExist:
            return JsonResponse({'error': 'Protocolo ou chave de acesso inválidos.'}, status=403)

        if report.status in ('resolvida', 'arquivada'):
            return JsonResponse({'error': 'Esta denúncia já foi encerrada.'}, status=400)

        ReportFollowUp.objects.create(
            report=report,
            mensagem=mensagem,
        )

        return JsonResponse({'success': True, 'message': 'Informação adicional registrada.'})


# ============================================================================
# VIEWS DO RH - Requerem autenticação e papel RH
# ============================================================================

class ReportListView(RHRequiredMixin, ListView):
    """Lista de denúncias para o RH gerenciar."""
    model = AnonymousReport
    template_name = 'reports/rh_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = AnonymousReport.objects.all()
        elif hasattr(user, 'profile'):
            qs = AnonymousReport.objects.filter(empresa__in=user.profile.empresas.all())
        else:
            qs = AnonymousReport.objects.none()

        # Filtros
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        categoria = self.request.GET.get('categoria')
        if categoria:
            qs = qs.filter(categoria=categoria)

        gravidade = self.request.GET.get('gravidade')
        if gravidade:
            qs = qs.filter(gravidade=gravidade)

        return qs.select_related('empresa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_superuser:
            base_qs = AnonymousReport.objects.all()
        elif hasattr(user, 'profile'):
            base_qs = AnonymousReport.objects.filter(empresa__in=user.profile.empresas.all())
        else:
            base_qs = AnonymousReport.objects.none()

        context['total_count'] = base_qs.count()
        context['abertas_count'] = base_qs.filter(status='aberta').count()
        context['em_analise_count'] = base_qs.filter(status='em_analise').count()
        context['investigando_count'] = base_qs.filter(status='investigando').count()
        context['resolvidas_count'] = base_qs.filter(status='resolvida').count()

        context['filter_status'] = self.request.GET.get('status', '')
        context['filter_categoria'] = self.request.GET.get('categoria', '')
        context['filter_gravidade'] = self.request.GET.get('gravidade', '')
        context['categorias'] = AnonymousReport.CATEGORIA_CHOICES
        context['gravidades'] = AnonymousReport.GRAVIDADE_CHOICES

        # Links públicos do canal de denúncias por empresa
        if user.is_superuser:
            empresas = Empresa.objects.filter(ativo=True)
        elif hasattr(user, 'profile'):
            empresas = user.profile.empresas.filter(ativo=True)
        else:
            empresas = Empresa.objects.none()

        canal_urls = []
        for empresa in empresas:
            path = reverse('reports:create', kwargs={'empresa_slug': empresa.slug})
            canal_urls.append({
                'empresa': empresa.nome,
                'url': self.request.build_absolute_uri(path),
            })
        context['canal_urls'] = canal_urls

        return context


class ReportDetailView(RHRequiredMixin, TemplateView):
    """Detalhe da denúncia para o RH."""
    template_name = 'reports/rh_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        report_id = self.kwargs.get('report_id')
        user = self.request.user

        if user.is_superuser:
            report = get_object_or_404(AnonymousReport, id=report_id)
        elif hasattr(user, 'profile'):
            report = get_object_or_404(
                AnonymousReport,
                id=report_id,
                empresa__in=user.profile.empresas.all()
            )
        else:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        context['report'] = report
        context['respostas'] = report.respostas_rh.select_related('respondido_por')
        context['followups'] = report.followups.all()
        context['status_choices'] = AnonymousReport.STATUS_CHOICES

        return context


class ReportRespondView(RHRequiredMixin, View):
    """RH responde a uma denúncia."""

    def post(self, request, report_id):
        user = request.user

        if user.is_superuser:
            report = get_object_or_404(AnonymousReport, id=report_id)
        elif hasattr(user, 'profile'):
            report = get_object_or_404(
                AnonymousReport,
                id=report_id,
                empresa__in=user.profile.empresas.all()
            )
        else:
            return JsonResponse({'error': 'Sem permissão.'}, status=403)

        mensagem = request.POST.get('mensagem', '').strip()
        novo_status = request.POST.get('novo_status', '').strip()
        visivel = request.POST.get('visivel_denunciante', 'on') == 'on'

        if not mensagem:
            messages.error(request, 'A mensagem é obrigatória.')
            return redirect('reports:rh_detail', report_id=report_id)

        response = ReportResponse.objects.create(
            report=report,
            mensagem=mensagem,
            respondido_por=user,
            novo_status=novo_status if novo_status else '',
            visivel_denunciante=visivel,
        )

        # Atualizar status do report se especificado
        if novo_status and novo_status in dict(AnonymousReport.STATUS_CHOICES):
            report.status = novo_status
            report.save(update_fields=['status', 'updated_at'])

        messages.success(request, 'Resposta registrada com sucesso.')
        return redirect('reports:rh_detail', report_id=report_id)
