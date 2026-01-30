from django.core.management.base import BaseCommand
from tasks.campaign_tasks import verificar_campanhas_expiradas


class Command(BaseCommand):
    help = 'Verifica e encerra campanhas que atingiram a data_fim'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando verificação de campanhas expiradas...')

        try:
            estatisticas = verificar_campanhas_expiradas()

            if estatisticas['campanhas_encerradas'] > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Concluído! {estatisticas['campanhas_encerradas']} campanha(s) encerrada(s), "
                        f"{estatisticas['total_convites_invalidados']} convite(s) invalidado(s)."
                    )
                )

                # Exibir detalhes
                for detalhe in estatisticas['detalhes']:
                    self.stdout.write(
                        f"  - {detalhe['campanha_nome']} ({detalhe['empresa']}): "
                        f"{detalhe['convites_invalidados']} convite(s) invalidado(s)"
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Concluído! Nenhuma campanha expirada encontrada.')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao verificar campanhas: {str(e)}')
            )
            raise
