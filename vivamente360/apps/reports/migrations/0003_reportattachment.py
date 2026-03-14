import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_rename_reports_ano_empresa_4f5c6a_idx_reports_ano_empresa_962fde_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('arquivo', models.FileField(help_text='Arquivo anexado à denúncia', upload_to='denuncias/%Y/%m/')),
                ('nome_original', models.CharField(help_text='Nome original do arquivo enviado', max_length=255)),
                ('tamanho', models.PositiveIntegerField(default=0, help_text='Tamanho do arquivo em bytes')),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='anexos', to='reports.anonymousreport')),
            ],
            options={
                'verbose_name': 'Anexo de Denúncia',
                'verbose_name_plural': 'Anexos de Denúncias',
                'db_table': 'reports_report_attachment',
                'ordering': ['created_at'],
            },
        ),
    ]
