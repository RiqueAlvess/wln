import time
from django.core.management.base import BaseCommand
from services.task_processors import TaskQueueWorker
from apps.core.models import UserNotification


class Command(BaseCommand):
    help = 'Processa todas as tarefas da fila (e-mails, análises IA, exports, etc.) e limpa notificações expiradas'

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
        parser.add_argument(
            '--cleanup-interval',
            type=int,
            default=3600,
            help='Intervalo em segundos para limpeza de notificações (padrão: 3600s / 1h)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        batch_size = options['batch_size']
        cleanup_interval = options['cleanup_interval']

        self.stdout.write(
            self.style.SUCCESS(
                f'Iniciando worker unificado de tarefas (intervalo: {interval}s, batch: {batch_size})...'
            )
        )
        self.stdout.write(self.style.WARNING('Tipos de tasks processadas: send_email, generate_sector_analysis, exports, imports'))
        self.stdout.write(self.style.WARNING(f'Limpeza de notificações a cada {cleanup_interval}s'))
        self.stdout.write(self.style.WARNING('Pressione Ctrl+C para parar'))

        last_cleanup = time.time()
        loop_count = 0

        while True:
            try:
                # Processar tasks pendentes
                processed = TaskQueueWorker.process_pending_tasks(limit=batch_size)

                if processed > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'[{time.strftime("%H:%M:%S")}] Processadas {processed} tarefas')
                    )

                # Verificar se é hora de limpar notificações expiradas
                current_time = time.time()
                if current_time - last_cleanup >= cleanup_interval:
                    deleted = UserNotification.objects.delete_expired()
                    if deleted > 0:
                        self.stdout.write(
                            self.style.WARNING(f'[{time.strftime("%H:%M:%S")}] {deleted} notificações expiradas deletadas')
                        )
                    last_cleanup = current_time

                time.sleep(interval)
                loop_count += 1

            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nWorker interrompido'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro: {str(e)}'))
                time.sleep(5)
