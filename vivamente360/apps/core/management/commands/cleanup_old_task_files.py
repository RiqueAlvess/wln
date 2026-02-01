"""
Comando Django para limpar arquivos antigos de tasks completadas.

Uso:
    python manage.py cleanup_old_task_files --days 30
"""
from django.core.management.base import BaseCommand
from services.task_file_storage import TaskFileStorage


class Command(BaseCommand):
    help = 'Remove arquivos de tasks mais antigos que X dias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de dias (padrão: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sem deletar arquivos'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'Modo simulação: encontrando arquivos mais antigos que {days} dias...'
                )
            )
            # TODO: Implementar dry-run
            self.stdout.write(
                self.style.WARNING('Modo dry-run não implementado completamente')
            )
            return

        self.stdout.write(f'Removendo arquivos mais antigos que {days} dias...')

        try:
            deleted_count = TaskFileStorage.cleanup_old_files(days=days)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Limpeza concluída: {deleted_count} arquivos removidos'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro durante limpeza: {str(e)}')
            )
