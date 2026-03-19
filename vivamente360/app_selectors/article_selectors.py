"""
Selectors para acesso aos dados de artigos.
Seguindo o padrão de separação entre camada de dados e views.
"""
from django.db.models import QuerySet, Q
from django.utils import timezone

from apps.articles.models import Artigo


def _publicados_qs():
    """Queryset base de artigos publicados (inclui os sem data definida)."""
    return Artigo.objects.filter(
        Q(status='published') &
        (Q(publicado_em__lte=timezone.now()) | Q(publicado_em__isnull=True))
    )


class ArticleSelectors:
    """Selectors para consultas relacionadas a artigos."""

    @staticmethod
    def get_publicados() -> QuerySet[Artigo]:
        """
        Retorna todos os artigos publicados, ordenados por data de publicação.
        """
        return _publicados_qs().select_related('autor').order_by('-publicado_em', '-created_at')

    @staticmethod
    def get_destaque() -> Artigo | None:
        """
        Retorna o artigo em destaque mais recente.
        Se houver múltiplos em destaque, retorna o mais recente.
        """
        return _publicados_qs().filter(
            destaque=True
        ).select_related('autor').order_by('-publicado_em', '-created_at').first()

    @staticmethod
    def get_recentes(limit: int = 6) -> QuerySet[Artigo]:
        """
        Retorna os artigos publicados mais recentes, excluindo o destaque.

        Args:
            limit: Número máximo de artigos a retornar (padrão: 6)
        """
        destaque = ArticleSelectors.get_destaque()
        queryset = _publicados_qs().select_related('autor')

        if destaque:
            queryset = queryset.exclude(pk=destaque.pk)

        return queryset.order_by('-publicado_em', '-created_at')[:limit]

    @staticmethod
    def get_por_categoria(categoria: str) -> QuerySet[Artigo]:
        """
        Retorna artigos publicados filtrados por categoria.

        Args:
            categoria: Código da categoria (nr1, saude, gestao, etc.)
        """
        return _publicados_qs().filter(
            categoria=categoria
        ).select_related('autor').order_by('-publicado_em', '-created_at')

    @staticmethod
    def get_by_slug(slug: str) -> Artigo | None:
        """
        Retorna um artigo publicado pelo slug.

        Args:
            slug: Slug do artigo
        """
        return Artigo.objects.filter(
            status='published',
            slug=slug
        ).select_related('autor').first()

    @staticmethod
    def buscar(query: str) -> QuerySet[Artigo]:
        """
        Busca artigos publicados por título, resumo ou conteúdo.

        Args:
            query: Termo de busca
        """
        return _publicados_qs().filter(
            Q(titulo__icontains=query) |
            Q(resumo__icontains=query) |
            Q(conteudo__icontains=query)
        ).select_related('autor').order_by('-publicado_em', '-created_at')

    @staticmethod
    def get_relacionados(artigo: Artigo, limit: int = 3) -> QuerySet[Artigo]:
        """
        Retorna artigos relacionados (mesma categoria, excluindo o artigo atual).

        Args:
            artigo: Artigo de referência
            limit: Número máximo de artigos relacionados
        """
        return _publicados_qs().filter(
            categoria=artigo.categoria
        ).exclude(
            pk=artigo.pk
        ).select_related('autor').order_by('-publicado_em', '-created_at')[:limit]

    @staticmethod
    def get_categorias_disponiveis() -> list[tuple[str, str]]:
        """
        Retorna lista de categorias que possuem artigos publicados.
        Retorna tuplas (código, nome_exibição).
        """
        categorias_com_artigos = Artigo.objects.filter(
            status='published'
        ).values_list('categoria', flat=True).distinct()

        categorias_dict = dict(Artigo.CATEGORIAS)
        return [
            (cat, categorias_dict[cat])
            for cat in categorias_com_artigos
            if cat in categorias_dict
        ]

    @staticmethod
    def get_mais_visualizados(limit: int = 5) -> QuerySet[Artigo]:
        """
        Retorna os artigos publicados mais visualizados.

        Args:
            limit: Número máximo de artigos a retornar
        """
        return _publicados_qs().select_related('autor').order_by('-visualizacoes', '-publicado_em')[:limit]
