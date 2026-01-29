"""
Views para gerenciamento e visualização de artigos.
"""
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.db.models import QuerySet

from apps.core.mixins import DashboardAccessMixin
from apps.articles.models import Artigo
from app_selectors.article_selectors import ArticleSelectors


class ArtigoListView(LoginRequiredMixin, DashboardAccessMixin, ListView):
    """
    View para listagem de artigos publicados.
    Exibe artigo em destaque e lista de artigos recentes.
    """
    model = Artigo
    template_name = 'articles/artigo_list.html'
    context_object_name = 'artigos'
    paginate_by = 12

    def get_queryset(self) -> QuerySet[Artigo]:
        """
        Retorna queryset de artigos baseado em filtros aplicados.
        """
        categoria = self.request.GET.get('categoria')
        busca = self.request.GET.get('q')

        if categoria:
            return ArticleSelectors.get_por_categoria(categoria)
        elif busca:
            return ArticleSelectors.buscar(busca)
        else:
            return ArticleSelectors.get_publicados()

    def get_context_data(self, **kwargs):
        """
        Adiciona contexto extra para o template.
        """
        context = super().get_context_data(**kwargs)

        # Artigo em destaque (apenas na primeira página e sem filtros)
        if not self.request.GET.get('page') and not self.request.GET.get('categoria') and not self.request.GET.get('q'):
            context['artigo_destaque'] = ArticleSelectors.get_destaque()

        # Categorias disponíveis para filtro
        context['categorias_disponiveis'] = ArticleSelectors.get_categorias_disponiveis()

        # Categoria selecionada
        context['categoria_selecionada'] = self.request.GET.get('categoria', '')

        # Termo de busca
        context['termo_busca'] = self.request.GET.get('q', '')

        # Artigos mais visualizados (sidebar)
        context['artigos_populares'] = ArticleSelectors.get_mais_visualizados(limit=5)

        return context


class ArtigoDetailView(LoginRequiredMixin, DashboardAccessMixin, DetailView):
    """
    View para visualização detalhada de um artigo.
    """
    model = Artigo
    template_name = 'articles/artigo_detail.html'
    context_object_name = 'artigo'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self) -> QuerySet[Artigo]:
        """
        Retorna apenas artigos publicados.
        """
        return Artigo.objects.filter(status='published').select_related('autor')

    def get_object(self, queryset=None):
        """
        Retorna o artigo e incrementa o contador de visualizações.
        """
        obj = super().get_object(queryset)

        # Incrementar visualizações
        obj.incrementar_visualizacao()

        return obj

    def get_context_data(self, **kwargs):
        """
        Adiciona contexto extra para o template.
        """
        context = super().get_context_data(**kwargs)

        # Artigos relacionados
        context['artigos_relacionados'] = ArticleSelectors.get_relacionados(
            self.object,
            limit=3
        )

        return context
