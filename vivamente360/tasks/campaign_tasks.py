from django.utils import timezone
from apps.surveys.models import Campaign
import logging

logger = logging.getLogger(__name__)


def verificar_campanhas_expiradas():
    """
    Task para encerrar automaticamente campanhas que atingiram a data_fim.

    Deve ser executada diariamente (ex: via cron ou scheduler).

    Returns:
        dict: Estatísticas da execução:
            - campanhas_encerradas (int): Número de campanhas encerradas
            - total_convites_invalidados (int): Total de convites invalidados
            - detalhes (list): Lista com detalhes de cada campanha encerrada
    """
    hoje = timezone.now().date()

    # Buscar campanhas ativas que já passaram da data_fim
    campanhas_expiradas = Campaign.objects.filter(
        status='active',
        data_fim__lt=hoje
    )

    estatisticas = {
        'campanhas_encerradas': 0,
        'total_convites_invalidados': 0,
        'detalhes': []
    }

    for campanha in campanhas_expiradas:
        try:
            # Encerrar campanha e invalidar convites
            resultado = campanha.encerrar()

            if resultado['success']:
                estatisticas['campanhas_encerradas'] += 1
                estatisticas['total_convites_invalidados'] += resultado['invalidated_count']

                detalhe = {
                    'campanha_id': campanha.id,
                    'campanha_nome': campanha.nome,
                    'empresa': campanha.empresa.nome,
                    'data_fim': str(campanha.data_fim),
                    'convites_invalidados': resultado['invalidated_count']
                }
                estatisticas['detalhes'].append(detalhe)

                logger.info(
                    f"Campanha {campanha.id} ({campanha.nome}) encerrada automaticamente. "
                    f"{resultado['invalidated_count']} convite(s) invalidado(s)."
                )
            else:
                logger.warning(
                    f"Campanha {campanha.id} ({campanha.nome}) não pôde ser encerrada: "
                    f"{resultado['message']}"
                )

        except Exception as e:
            logger.error(
                f"Erro ao encerrar campanha {campanha.id} ({campanha.nome}): {str(e)}",
                exc_info=True
            )

    # Log final
    if estatisticas['campanhas_encerradas'] > 0:
        logger.info(
            f"Task concluída: {estatisticas['campanhas_encerradas']} campanha(s) encerrada(s), "
            f"{estatisticas['total_convites_invalidados']} convite(s) invalidado(s)."
        )
    else:
        logger.info("Task concluída: Nenhuma campanha expirada encontrada.")

    return estatisticas
