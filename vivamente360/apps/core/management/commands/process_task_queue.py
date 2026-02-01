"""
Comando Django para processar tarefas da fila do banco de dados.

Uso:
    # Processar uma vez
    python manage.py process_task_queue

    # Processar continuamente (worker mode)
    python manage.py process_task_queue --worker

    # Processar com intervalo customizado
    python manage.py process_task_queue --worker --interval 30

    # Processar mais tarefas por batch
    python manage.py process_task_queue --worker --batch-size 20
"""
from django.core.management.base import BaseCommand
from services.task_processors import TaskQueueWorker
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Processa tarefas pendentes da fila do banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--worker',
            action='store_true',
            help='Executar em modo worker contínuo'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Intervalo em segundos entre processamentos (modo worker)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Número de tarefas a processar por batch'
        )
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='Tentar reprocessar tarefas falhadas'
        )

    def handle(self, *args, **options):
        worker_mode = options['worker']
        interval = options['interval']
        batch_size = options['batch_size']
        retry_failed = options['retry_failed']

        if worker_mode:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Iniciando worker de tarefas (intervalo: {interval}s, batch: {batch_size})'
                )
            )
            self.run_worker(interval, batch_size, retry_failed)
        else:
            self.stdout.write('Processando tarefas pendentes...')
            processed = TaskQueueWorker.process_pending_tasks(limit=batch_size)
            self.stdout.write(
                self.style.SUCCESS(f'Processadas {processed} tarefas com sucesso')
            )

            if retry_failed:
                retried = TaskQueueWorker.retry_failed_tasks()
                self.stdout.write(
                    self.style.WARNING(f'{retried} tarefas falhadas marcadas para retry')
                )

    def run_worker(self, interval, batch_size, retry_failed):
        """Executa worker em loop contínuo."""
        self.stdout.write(self.style.WARNING('Pressione Ctrl+C para parar'))

        try:
            while True:
                # Processar tarefas pendentes
                processed = TaskQueueWorker.process_pending_tasks(limit=batch_size)

                if processed > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'[{time.strftime("%H:%M:%S")}] Processadas {processed} tarefas')
                    )

                # Retry de tarefas falhadas (se habilitado)
                if retry_failed:
                    retried = TaskQueueWorker.retry_failed_tasks(limit=5)
                    if retried > 0:
                        self.stdout.write(
                            self.style.WARNING(f'[{time.strftime("%H:%M:%S")}] {retried} tarefas marcadas para retry')
                        )

                # Aguardar intervalo
                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nWorker interrompido pelo usuário'))
            return
