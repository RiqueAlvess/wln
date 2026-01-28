"""
Management command para processar notificações do sistema Vivamente360.

Este comando executa as tasks de verificação e envio de notificações:
- Processa fila de emails pendentes
- Verifica adesão de campanhas ativas
- Verifica prazos de planos de ação
- Verifica riscos críticos em respostas recentes

Uso:
    python manage.py process_notifications
    python manage.py process_notifications --check-adhesion
    python manage.py process_notifications --check-deadlines
    python manage.py process_notifications --check-risks
    python manage.py process_notifications --all
"""

from django.core.management.base import BaseCommand
from tasks.notification_tasks import (
    process_notification_queue,
    check_campaign_adhesion,
    check_action_plan_deadlines,
    check_critical_risks
)


class Command(BaseCommand):
    help = 'Processa notificações pendentes e verifica alertas automáticos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-adhesion',
            action='store_true',
            help='Verifica adesão de campanhas ativas',
        )
        parser.add_argument(
            '--check-deadlines',
            action='store_true',
            help='Verifica prazos de planos de ação',
        )
        parser.add_argument(
            '--check-risks',
            action='store_true',
            help='Verifica riscos críticos em respostas recentes',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Executa todas as verificações',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Número de notificações a processar por vez (padrão: 10)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando processamento de notificações...'))

        # Sempre processa a fila de emails pendentes
        self.stdout.write('Processando fila de emails...')
        result = process_notification_queue(batch_size=options['batch_size'])
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Fila processada: {result['success']} enviados, "
                f"{result['failed']} falharam, {result['skipped']} ignorados"
            )
        )

        # Verificações opcionais
        if options['check_adhesion'] or options['all']:
            self.stdout.write('Verificando adesão de campanhas...')
            result = check_campaign_adhesion()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Campanhas verificadas: {result['campaigns_checked']}, "
                    f"alertas enviados: {result['alerts_sent']}"
                )
            )

        if options['check_deadlines'] or options['all']:
            self.stdout.write('Verificando prazos de planos de ação...')
            result = check_action_plan_deadlines()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Planos verificados: {result['plans_checked']}, "
                    f"alertas enviados: {result['alerts_sent']}"
                )
            )

        if options['check_risks'] or options['all']:
            self.stdout.write('Verificando riscos críticos...')
            result = check_critical_risks()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Respostas verificadas: {result['responses_checked']}, "
                    f"alertas enviados: {result['alerts_sent']}"
                )
            )

        self.stdout.write(self.style.SUCCESS('\n✓ Processamento de notificações concluído!'))
