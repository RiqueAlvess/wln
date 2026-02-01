# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenants', '0001_initial'),
        ('core', '0003_remove_lgpdcomplianceitem'),
    ]

    operations = [
        # Adicionar novos campos ao TaskQueue
        migrations.AddField(
            model_name='taskqueue',
            name='file_path',
            field=models.CharField(blank=True, help_text='Caminho do arquivo gerado', max_length=500),
        ),
        migrations.AddField(
            model_name='taskqueue',
            name='file_name',
            field=models.CharField(blank=True, help_text='Nome do arquivo para download', max_length=255),
        ),
        migrations.AddField(
            model_name='taskqueue',
            name='file_size',
            field=models.IntegerField(blank=True, help_text='Tamanho do arquivo em bytes', null=True),
        ),
        migrations.AddField(
            model_name='taskqueue',
            name='progress',
            field=models.IntegerField(default=0, help_text='Progresso da task (0-100)'),
        ),
        migrations.AddField(
            model_name='taskqueue',
            name='progress_message',
            field=models.CharField(blank=True, help_text='Mensagem de progresso', max_length=255),
        ),
        migrations.AddField(
            model_name='taskqueue',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='taskqueue',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tenants.empresa'),
        ),

        # Adicionar índices
        migrations.AddIndex(
            model_name='taskqueue',
            index=models.Index(fields=['user', 'status'], name='core_task_q_user_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='taskqueue',
            index=models.Index(fields=['empresa', 'status'], name='core_task_q_empresa_status_idx'),
        ),

        # Criar modelo UserNotification
        migrations.CreateModel(
            name='UserNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('task_completed', 'Task Completada'), ('task_failed', 'Task Falhou'), ('file_ready', 'Arquivo Pronto'), ('info', 'Informação'), ('warning', 'Aviso'), ('error', 'Erro')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('link_url', models.CharField(blank=True, max_length=500)),
                ('link_text', models.CharField(blank=True, max_length=100)),
                ('is_read', models.BooleanField(default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('empresa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tenants.empresa')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.taskqueue')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'core_user_notification',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='usernotification',
            index=models.Index(fields=['user', 'is_read', '-created_at'], name='core_user_n_user_id_is_read_idx'),
        ),
    ]
