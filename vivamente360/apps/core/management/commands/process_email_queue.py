import time
from django.core.management.base import BaseCommand
from tasks.email_tasks import process_email_queue


class Command(BaseCommand):
    help = 'Processa fila de e-mails'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando worker de e-mails...')

        while True:
            try:
                process_email_queue()
                time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('Worker interrompido'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro: {str(e)}'))
                time.sleep(5)
