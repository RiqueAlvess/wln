from django.views.generic import ListView, View, CreateView, UpdateView
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Q, Max
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from apps.core.mixins import RHRequiredMixin
from apps.actions.models import PlanoAcao, ChecklistNR1Etapa, EvidenciaNR1
from apps.surveys.models import Campaign
from services.export_service import ExportService
from .serializers import (
    PlanoAcaoSerializer,
    ChecklistNR1EtapaSerializer,
    EvidenciaNR1Serializer,
    ChecklistNR1ResumoSerializer
)
from .forms import PlanoAcaoForm
from io import BytesIO
import json


class PlanoAcaoListView(RHRequiredMixin, ListView):
    model = PlanoAcao
    template_name = 'actions/plano_acao_list.html'
    context_object_name = 'planos'
    paginate_by = 25

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        return PlanoAcao.objects.filter(campaign_id=campaign_id).select_related('dimensao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        context['campaign'] = get_object_or_404(Campaign, id=campaign_id)
        return context


class PlanoAcaoCreateView(RHRequiredMixin, CreateView):
    """
    View para criar novo Plano de Ação com editor rico
    """
    model = PlanoAcao
    form_class = PlanoAcaoForm
    template_name = 'actions/plano_acao_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        campaign_id = self.kwargs['campaign_id']
        campaign = get_object_or_404(Campaign, id=campaign_id)
        kwargs['campaign'] = campaign
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        context['campaign'] = get_object_or_404(Campaign, id=campaign_id)
        return context

    def form_valid(self, form):
        campaign_id = self.kwargs['campaign_id']
        campaign = get_object_or_404(Campaign, id=campaign_id)

        plano = form.save(commit=False)
        plano.empresa = self.request.user.empresa
        plano.campaign = campaign
        plano.save()

        return redirect('actions:plano_acao_list', campaign_id=campaign_id)

    def get_success_url(self):
        return reverse('actions:plano_acao_list', kwargs={'campaign_id': self.kwargs['campaign_id']})


class PlanoAcaoUpdateView(RHRequiredMixin, UpdateView):
    """
    View para editar Plano de Ação existente
    """
    model = PlanoAcao
    form_class = PlanoAcaoForm
    template_name = 'actions/plano_acao_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        campaign_id = self.kwargs['campaign_id']
        campaign = get_object_or_404(Campaign, id=campaign_id)
        kwargs['campaign'] = campaign
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        context['campaign'] = get_object_or_404(Campaign, id=campaign_id)
        return context

    def get_success_url(self):
        return reverse('actions:plano_acao_list', kwargs={'campaign_id': self.kwargs['campaign_id']})


class PlanoAcaoAutoSaveView(RHRequiredMixin, View):
    """
    View para auto-save do conteúdo do editor (AJAX)
    """
    def post(self, request, campaign_id, pk):
        if pk == '0':
            # Novo plano de ação - criar rascunho
            plano = PlanoAcao(
                empresa=request.user.empresa,
                campaign_id=campaign_id,
                status='pendente'
            )
        else:
            plano = get_object_or_404(PlanoAcao, id=pk, campaign_id=campaign_id)

        # Atualizar campos do editor
        if 'conteudo_estruturado' in request.POST:
            try:
                plano.conteudo_estruturado = json.loads(request.POST.get('conteudo_estruturado'))
            except json.JSONDecodeError:
                pass

        if 'conteudo_html' in request.POST:
            plano.conteudo_html = request.POST.get('conteudo_html')

        # Atualizar outros campos se presentes
        if 'dimensao' in request.POST and request.POST.get('dimensao'):
            plano.dimensao_id = request.POST.get('dimensao')

        if 'nivel_risco' in request.POST and request.POST.get('nivel_risco'):
            plano.nivel_risco = request.POST.get('nivel_risco')

        if 'responsavel' in request.POST and request.POST.get('responsavel'):
            plano.responsavel = request.POST.get('responsavel')

        if 'prazo' in request.POST and request.POST.get('prazo'):
            plano.prazo = request.POST.get('prazo')

        plano.save()

        return JsonResponse({
            'success': True,
            'plano_id': plano.id,
            'message': 'Rascunho salvo automaticamente'
        })


class ExportPlanoAcaoWordView(RHRequiredMixin, View):
    """
    Exporta lista de planos de ação (formato legado)
    """
    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        planos = PlanoAcao.objects.filter(campaign=campaign).select_related('dimensao')

        doc = ExportService.export_plano_acao_word(campaign, planos)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename=plano_acao_{campaign.nome}.docx'
        doc.save(response)

        return response


class ExportPlanoAcaoRichWordView(RHRequiredMixin, View):
    """
    Exporta um único plano de ação com conteúdo rico do editor TipTap
    """
    def get(self, request, campaign_id, pk):
        plano = get_object_or_404(
            PlanoAcao,
            id=pk,
            campaign_id=campaign_id
        )

        doc = ExportService.export_plano_acao_rich_word(plano)

        # Salvar em buffer
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        filename = f'plano_acao_{plano.dimensao.nome}_{plano.id}.docx'
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


# ============================================================================
# COMPLIANCE NR-1 VIEWS
# ============================================================================

class ChecklistNR1ListView(RHRequiredMixin, ListView):
    """
    View para listar e visualizar o checklist de compliance NR-1.
    """
    model = ChecklistNR1Etapa
    template_name = 'actions/checklist_nr1.html'
    context_object_name = 'itens'

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        return ChecklistNR1Etapa.objects.filter(
            campaign_id=campaign_id
        ).prefetch_related('evidencias').order_by('etapa', 'item_ordem')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = self.kwargs['campaign_id']
        campaign = get_object_or_404(Campaign, id=campaign_id)

        # Verificar se existem itens do checklist para esta campanha
        # Se não existirem, criar os itens padrão
        if not ChecklistNR1Etapa.objects.filter(campaign=campaign).exists():
            self._criar_checklist_padrao(campaign)

        # Organizar itens por etapa
        itens_por_etapa = {}
        for etapa_num, etapa_nome in ChecklistNR1Etapa.ETAPAS:
            itens = self.get_queryset().filter(etapa=etapa_num)
            total = itens.count()
            concluidos = itens.filter(concluido=True).count()
            progresso = (concluidos / total * 100) if total > 0 else 0

            itens_por_etapa[etapa_num] = {
                'nome': etapa_nome,
                'itens': itens,
                'total': total,
                'concluidos': concluidos,
                'progresso': progresso
            }

        # Calcular progresso geral
        total_itens = self.get_queryset().count()
        total_concluidos = self.get_queryset().filter(concluido=True).count()
        progresso_geral = (total_concluidos / total_itens * 100) if total_itens > 0 else 0

        context['campaign'] = campaign
        context['itens_por_etapa'] = itens_por_etapa
        context['progresso_geral'] = progresso_geral
        context['total_itens'] = total_itens
        context['total_concluidos'] = total_concluidos

        return context

    def _criar_checklist_padrao(self, campaign):
        """
        Cria os itens padrão do checklist NR-1 para uma campanha
        """
        # Itens padrão do checklist NR-1
        itens_padrao = [
            # Etapa 1: Preparação
            (1, 1, "Definir equipe responsável pela avaliação", False),
            (1, 2, "Comunicar colaboradores sobre a pesquisa", False),
            (1, 3, "Garantir anonimato e confidencialidade", False),
            (1, 4, "Selecionar instrumento de avaliação (HSE-IT)", True),
            (1, 5, "Definir cronograma de aplicação", False),

            # Etapa 2: Identificação de Perigos
            (2, 1, "Mapear setores e cargos da empresa", False),
            (2, 2, "Identificar fatores de risco por área", False),
            (2, 3, "Levantar histórico de afastamentos", False),
            (2, 4, "Consultar PCMSO e ASO existentes", False),

            # Etapa 3: Avaliação de Riscos
            (3, 1, "Aplicar questionário HSE-IT", True),
            (3, 2, "Calcular scores por dimensão", True),
            (3, 3, "Classificar níveis de risco (Matriz P×S)", False),
            (3, 4, "Priorizar áreas de intervenção", False),

            # Etapa 4: Planejamento e Controle
            (4, 1, "Elaborar planos de ação para riscos críticos", False),
            (4, 2, "Definir responsáveis e prazos", False),
            (4, 3, "Alocar recursos necessários", False),
            (4, 4, "Estabelecer indicadores de acompanhamento", False),

            # Etapa 5: Monitoramento e Revisão
            (5, 1, "Acompanhar execução dos planos de ação", False),
            (5, 2, "Reavaliar riscos periodicamente", False),
            (5, 3, "Revisar eficácia das intervenções", False),
            (5, 4, "Ajustar estratégias conforme necessário", False),

            # Etapa 6: Comunicação e Cultura
            (6, 1, "Divulgar resultados aos colaboradores", False),
            (6, 2, "Promover treinamentos sobre saúde mental", False),
            (6, 3, "Fortalecer canais de comunicação interna", False),
            (6, 4, "Fomentar cultura de prevenção e bem-estar", False),
        ]

        for etapa, ordem, texto, automatico in itens_padrao:
            item = ChecklistNR1Etapa.objects.create(
                campaign=campaign,
                empresa=campaign.empresa,
                etapa=etapa,
                item_ordem=ordem,
                item_texto=texto,
                automatico=automatico,
                concluido=automatico
            )
            if automatico:
                item.data_conclusao = timezone.now()
                item.save()


class ChecklistNR1ItemUpdateView(RHRequiredMixin, View):
    """
    View para atualizar um item do checklist (marcar como concluído, adicionar responsável, etc.)
    """
    def post(self, request, item_id):
        item = get_object_or_404(ChecklistNR1Etapa, id=item_id)

        # Atualizar campos
        concluido = request.POST.get('concluido') == 'true'
        item.concluido = concluido

        if concluido and not item.data_conclusao:
            item.data_conclusao = timezone.now()
        elif not concluido:
            item.data_conclusao = None

        if 'responsavel' in request.POST:
            item.responsavel = request.POST.get('responsavel', '')

        if 'prazo' in request.POST:
            prazo = request.POST.get('prazo')
            item.prazo = prazo if prazo else None

        if 'observacoes' in request.POST:
            item.observacoes = request.POST.get('observacoes', '')

        item.save()

        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'concluido': item.concluido,
            'data_conclusao': item.data_conclusao.isoformat() if item.data_conclusao else None,
            'progresso_etapa': item.get_progresso_etapa()
        })


class EvidenciaNR1UploadView(RHRequiredMixin, View):
    """
    View para fazer upload de evidências
    """
    def post(self, request, item_id):
        item = get_object_or_404(ChecklistNR1Etapa, id=item_id)

        if 'arquivo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'Nenhum arquivo enviado'}, status=400)

        arquivo = request.FILES['arquivo']
        tipo = request.POST.get('tipo', 'outro')
        descricao = request.POST.get('descricao', '')

        # Validar tamanho do arquivo (máximo 10MB)
        if arquivo.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Arquivo muito grande (máximo 10MB)'}, status=400)

        # Criar evidência
        evidencia = EvidenciaNR1.objects.create(
            checklist_item=item,
            campaign=item.campaign,
            empresa=item.empresa,
            uploaded_by=request.user,
            arquivo=arquivo,
            nome_original=arquivo.name,
            tipo=tipo,
            tamanho_bytes=arquivo.size,
            descricao=descricao
        )

        return JsonResponse({
            'success': True,
            'evidencia': {
                'id': evidencia.id,
                'nome_original': evidencia.nome_original,
                'tipo': evidencia.get_tipo_display(),
                'tamanho': evidencia.get_tamanho_formatado(),
                'descricao': evidencia.descricao,
                'uploaded_by': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'created_at': evidencia.created_at.strftime('%d/%m/%Y %H:%M'),
                'arquivo_url': evidencia.arquivo.url
            }
        })


class EvidenciaNR1DeleteView(RHRequiredMixin, View):
    """
    View para deletar uma evidência
    """
    def post(self, request, evidencia_id):
        evidencia = get_object_or_404(EvidenciaNR1, id=evidencia_id)

        # Deletar arquivo físico
        if evidencia.arquivo:
            evidencia.arquivo.delete(save=False)

        # Deletar registro
        evidencia.delete()

        return JsonResponse({'success': True})


class ChecklistNR1ExportPDFView(RHRequiredMixin, View):
    """
    View para exportar o checklist completo em PDF
    """
    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        itens = ChecklistNR1Etapa.objects.filter(
            campaign=campaign
        ).prefetch_related('evidencias').order_by('etapa', 'item_ordem')

        # Organizar itens por etapa
        itens_por_etapa = {}
        for etapa_num, etapa_nome in ChecklistNR1Etapa.ETAPAS:
            itens_etapa = itens.filter(etapa=etapa_num)
            total = itens_etapa.count()
            concluidos = itens_etapa.filter(concluido=True).count()
            progresso = (concluidos / total * 100) if total > 0 else 0

            itens_por_etapa[etapa_num] = {
                'nome': etapa_nome,
                'itens': itens_etapa,
                'total': total,
                'concluidos': concluidos,
                'progresso': progresso
            }

        # Calcular progresso geral
        total_itens = itens.count()
        total_concluidos = itens.filter(concluido=True).count()
        progresso_geral = (total_concluidos / total_itens * 100) if total_itens > 0 else 0

        # Gerar PDF
        pdf = ExportService.export_checklist_nr1_pdf(
            campaign, itens_por_etapa, progresso_geral, total_itens, total_concluidos
        )

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=checklist_nr1_{campaign.nome}.pdf'

        return response


# ============================================================================
# API REST VIEWSETS
# ============================================================================

class ChecklistNR1ViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar itens do checklist NR-1 via API REST
    """
    serializer_class = ChecklistNR1EtapaSerializer
    filterset_fields = ['campaign', 'empresa', 'etapa', 'concluido']
    ordering_fields = ['etapa', 'item_ordem', 'prazo', 'updated_at']
    ordering = ['etapa', 'item_ordem']

    def get_queryset(self):
        return ChecklistNR1Etapa.objects.all().prefetch_related('evidencias')

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        """
        Endpoint para obter resumo do checklist de uma campanha
        """
        campaign_id = request.query_params.get('campaign_id')
        if not campaign_id:
            return Response(
                {'error': 'campaign_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign = get_object_or_404(Campaign, id=campaign_id)
        itens = ChecklistNR1Etapa.objects.filter(campaign=campaign)

        total_itens = itens.count()
        itens_concluidos = itens.filter(concluido=True).count()
        progresso_geral = (itens_concluidos / total_itens * 100) if total_itens > 0 else 0

        # Resumo por etapa
        etapas_resumo = []
        for etapa_num, etapa_nome in ChecklistNR1Etapa.ETAPAS:
            itens_etapa = itens.filter(etapa=etapa_num)
            total = itens_etapa.count()
            concluidos = itens_etapa.filter(concluido=True).count()
            progresso = (concluidos / total * 100) if total > 0 else 0

            etapas_resumo.append({
                'etapa': etapa_num,
                'nome': etapa_nome,
                'total': total,
                'concluidos': concluidos,
                'progresso': progresso
            })

        data = {
            'campaign_id': campaign.id,
            'campaign_nome': campaign.nome,
            'total_itens': total_itens,
            'itens_concluidos': itens_concluidos,
            'progresso_geral': progresso_geral,
            'etapas': etapas_resumo,
            'ultima_atualizacao': itens.aggregate(Max('updated_at'))['updated_at__max']
        }

        serializer = ChecklistNR1ResumoSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def marcar_concluido(self, request, pk=None):
        """
        Endpoint para marcar um item como concluído/não concluído
        """
        item = self.get_object()
        concluido = request.data.get('concluido', True)

        item.concluido = concluido
        if concluido and not item.data_conclusao:
            item.data_conclusao = timezone.now()
        elif not concluido:
            item.data_conclusao = None

        item.save()

        serializer = self.get_serializer(item)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def criar_padrao(self, request):
        """
        Endpoint para criar checklist padrão NR-1 para uma campanha
        """
        campaign_id = request.data.get('campaign_id')
        if not campaign_id:
            return Response(
                {'error': 'campaign_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign = get_object_or_404(Campaign, id=campaign_id)

        # Verificar se já existe checklist para esta campanha
        if ChecklistNR1Etapa.objects.filter(campaign=campaign).exists():
            return Response(
                {'error': 'Checklist já existe para esta campanha'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Criar itens padrão do checklist NR-1
        itens_padrao = [
            # Etapa 1: Preparação
            (1, 1, "Definir equipe responsável pela avaliação", False),
            (1, 2, "Comunicar colaboradores sobre a pesquisa", False),
            (1, 3, "Garantir anonimato e confidencialidade", False),
            (1, 4, "Selecionar instrumento de avaliação (HSE-IT)", True),
            (1, 5, "Definir cronograma de aplicação", False),

            # Etapa 2: Identificação de Perigos
            (2, 1, "Mapear setores e cargos da empresa", False),
            (2, 2, "Identificar fatores de risco por área", False),
            (2, 3, "Levantar histórico de afastamentos", False),
            (2, 4, "Consultar PCMSO e ASO existentes", False),

            # Etapa 3: Avaliação de Riscos
            (3, 1, "Aplicar questionário HSE-IT", True),
            (3, 2, "Calcular scores por dimensão", True),
            (3, 3, "Classificar níveis de risco (Matriz P×S)", False),
            (3, 4, "Priorizar áreas de intervenção", False),

            # Etapa 4: Planejamento e Controle
            (4, 1, "Elaborar planos de ação para riscos críticos", False),
            (4, 2, "Definir responsáveis e prazos", False),
            (4, 3, "Alocar recursos necessários", False),
            (4, 4, "Estabelecer indicadores de acompanhamento", False),

            # Etapa 5: Monitoramento e Revisão
            (5, 1, "Acompanhar execução dos planos de ação", False),
            (5, 2, "Reavaliar riscos periodicamente", False),
            (5, 3, "Revisar eficácia das intervenções", False),
            (5, 4, "Ajustar estratégias conforme necessário", False),

            # Etapa 6: Comunicação e Cultura
            (6, 1, "Divulgar resultados aos colaboradores", False),
            (6, 2, "Promover treinamentos sobre saúde mental", False),
            (6, 3, "Fortalecer canais de comunicação interna", False),
            (6, 4, "Fomentar cultura de prevenção e bem-estar", False),
        ]

        itens_criados = []
        for etapa, ordem, texto, automatico in itens_padrao:
            item = ChecklistNR1Etapa.objects.create(
                campaign=campaign,
                empresa=campaign.empresa,
                etapa=etapa,
                item_ordem=ordem,
                item_texto=texto,
                automatico=automatico,
                concluido=automatico  # Itens automáticos já vêm marcados como concluídos
            )
            if automatico:
                item.data_conclusao = timezone.now()
                item.save()

            itens_criados.append(item)

        serializer = self.get_serializer(itens_criados, many=True)
        return Response({
            'success': True,
            'message': f'{len(itens_criados)} itens criados com sucesso',
            'itens': serializer.data
        }, status=status.HTTP_201_CREATED)


class EvidenciaNR1ViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar evidências NR-1 via API REST
    """
    serializer_class = EvidenciaNR1Serializer
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['checklist_item', 'campaign', 'empresa', 'tipo']
    ordering_fields = ['created_at', 'nome_original']
    ordering = ['-created_at']

    def get_queryset(self):
        return EvidenciaNR1.objects.all().select_related('checklist_item', 'campaign', 'empresa', 'uploaded_by')

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
