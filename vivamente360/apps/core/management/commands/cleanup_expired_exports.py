"""
Comando Django para limpar arquivos exportados expirados (> 48 horas).

Este comando remove arquivos de exportações que excederam seu TTL de 48 horas,
liberando espaço em disco e mantendo o sistema organizado.

Uso:
    python manage.py cleanup_expired_exports
    python manage.py cleanup_expired_exports --dry-run
    python manage.py cleanup_expired_exports --force  # Remove mesmo não expirados
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.storage import default_storage
from apps.core.models import ExportedFile, TaskQueue
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove arquivos exportados expirados (TTL de 48 horas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sem deletar arquivos'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Remove também arquivos não expirados (usa 30 dias como limite)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        now = timezone.now()

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Modo simulação: nenhum arquivo será deletado')
            )

        # Buscar arquivos expirados do model ExportedFile
        if force:
            # Forçar limpeza de arquivos antigos (> 30 dias)
            from datetime import timedelta
            cutoff = now - timedelta(days=30)
            exported_files = ExportedFile.objects.filter(
                created_at__lt=cutoff
            )
            self.stdout.write(f'Removendo arquivos criados há mais de 30 dias (modo force)...')
        else:
            # Limpeza normal: apenas expirados (> 48h)
            exported_files = ExportedFile.objects.filter(
                expires_at__lt=now,
                status__in=['completed', 'pending', 'processing']
            )
            self.stdout.write(f'Removendo arquivos expirados (> 48 horas)...')

        count = 0
        errors = 0

        for export_file in exported_files:
            try:
                # Buscar o arquivo físico através da task relacionada
                task = export_file.task

                if task.file_path:
                    if dry_run:
                        self.stdout.write(
                            self.style.NOTICE(f'[DRY-RUN] Removeria: {task.file_path}')
                        )
                    else:
                        # Deletar arquivo físico se existir
                        if default_storage.exists(task.file_path):
                            default_storage.delete(task.file_path)
                            self.stdout.write(
                                self.style.SUCCESS(f'✓ Arquivo deletado: {task.file_path}')
                            )

                        # Limpar campos do task
                        task.file_path = ''
                        task.file_name = ''
                        task.file_size = None
                        task.save(update_fields=['file_path', 'file_name', 'file_size'])

                if not dry_run:
                    # Marcar como expirado
                    export_file.mark_expired()

                count += 1

            except Exception as e:
                errors += 1
                logger.error(f"Erro ao limpar arquivo {export_file.id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f'✗ Erro ao processar arquivo {export_file.id}: {str(e)}')
                )

        # Também limpar tasks antigas sem ExportedFile associado
        self.stdout.write('\nLimpando tasks antigas sem ExportedFile...')

        from datetime import timedelta
        old_cutoff = now - timedelta(days=7)  # Tasks com mais de 7 dias

        old_tasks = TaskQueue.objects.filter(
            completed_at__lt=old_cutoff,
            file_path__isnull=False,
            status='completed'
        ).exclude(
            file_path=''
        ).exclude(
            id__in=ExportedFile.objects.values_list('task_id', flat=True)
        )

        task_count = 0
        for task in old_tasks:
            try:
                if task.file_path:
                    if dry_run:
                        self.stdout.write(
                            self.style.NOTICE(f'[DRY-RUN] Removeria task file: {task.file_path}')
                        )
                    else:
                        if default_storage.exists(task.file_path):
                            default_storage.delete(task.file_path)

                        task.file_path = ''
                        task.file_name = ''
                        task.file_size = None
                        task.save(update_fields=['file_path', 'file_name', 'file_size'])

                task_count += 1

            except Exception as e:
                errors += 1
                logger.error(f"Erro ao limpar task {task.id}: {str(e)}")

        # Relatório final
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'SIMULAÇÃO: {count} ExportedFiles e {task_count} tasks antigas seriam removidos'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Limpeza concluída: {count} ExportedFiles e {task_count} tasks antigas removidos'
                )
            )

        if errors > 0:
            self.stdout.write(
                self.style.ERROR(f'Erros: {errors}')
            )

        self.stdout.write('='*60)
