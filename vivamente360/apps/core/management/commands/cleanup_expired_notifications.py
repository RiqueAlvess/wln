"""
Comando Django para deletar notificações expiradas (mais antigas que 24 horas).

Uso:
    python manage.py cleanup_expired_notifications
"""
from django.core.management.base import BaseCommand
from apps.core.models import UserNotification


class Command(BaseCommand):
    help = 'Deleta notificações mais antigas que 24 horas'

    def handle(self, *args, **options):
        self.stdout.write('Deletando notificações expiradas...')

        try:
            deleted = UserNotification.objects.delete_expired()

            if deleted > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Limpeza concluída: {deleted} notificações deletadas'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Nenhuma notificação expirada encontrada')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro durante limpeza: {str(e)}')
            )
