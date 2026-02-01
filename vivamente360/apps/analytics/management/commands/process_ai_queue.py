import time
from django.core.management.base import BaseCommand
from tasks.ai_analysis_tasks import process_sector_analysis_queue


class Command(BaseCommand):
    help = 'Processa fila de análises de IA'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando worker de análises IA...')

        while True:
            try:
                processed = process_sector_analysis_queue()
                if not processed:
                    time.sleep(2)  # Aguardar se não houver tarefas
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('Worker interrompido'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro: {str(e)}'))
                time.sleep(5)
