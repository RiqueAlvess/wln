# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_expand_taskqueue_and_add_notifications'),
        ('tenants', '0001_initial'),
        ('surveys', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExportedFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tipo', models.CharField(choices=[('excel', 'Excel'), ('pdf', 'PDF'), ('word', 'Word'), ('txt', 'Texto')], max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('processing', 'Processando'), ('completed', 'Concluído'), ('failed', 'Falhou'), ('expired', 'Expirado')], default='pending', max_length=15)),
                ('expires_at', models.DateTimeField(help_text='Data e hora em que o arquivo expira e deve ser removido')),
                ('downloaded_at', models.DateTimeField(blank=True, help_text='Primeira vez que o arquivo foi baixado', null=True)),
                ('download_count', models.IntegerField(default=0, help_text='Número de vezes que o arquivo foi baixado')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='surveys.campaign')),
                ('empresa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tenants.empresa')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='exported_file', to='core.taskqueue')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exported_files', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'core_exported_file',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='exportedfile',
            index=models.Index(fields=['user', 'status', 'expires_at'], name='core_export_user_id_status_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='exportedfile',
            index=models.Index(fields=['status', 'expires_at'], name='core_export_status_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='exportedfile',
            index=models.Index(fields=['empresa', 'status'], name='core_export_empresa_status_idx'),
        ),
    ]
