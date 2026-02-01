import time
from django.core.management.base import BaseCommand
from services.task_processors import TaskQueueWorker


class Command(BaseCommand):
    help = 'Processa todas as tarefas da fila (e-mails, análises IA, exports, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=1,
            help='Intervalo em segundos entre processamentos (padrão: 1s)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Número de tarefas a processar por batch (padrão: 10)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        batch_size = options['batch_size']

        self.stdout.write(
            self.style.SUCCESS(
                f'Iniciando worker unificado de tarefas (intervalo: {interval}s, batch: {batch_size})...'
            )
        )
        self.stdout.write(self.style.WARNING('Tipos de tasks processadas: send_email, generate_sector_analysis, exports, imports'))
        self.stdout.write(self.style.WARNING('Pressione Ctrl+C para parar'))

        while True:
            try:
                # Processar tasks pendentes
                processed = TaskQueueWorker.process_pending_tasks(limit=batch_size)

                if processed > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'[{time.strftime("%H:%M:%S")}] Processadas {processed} tarefas')
                    )

                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nWorker interrompido'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro: {str(e)}'))
                time.sleep(5)
