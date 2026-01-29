# Generated manually for NR-1 Compliance Checklist

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0002_remove_evidencia_checklist'),
        ('surveys', '0001_initial'),
        ('tenants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChecklistNR1Etapa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('etapa', models.IntegerField(choices=[
                    (1, 'Preparação'),
                    (2, 'Identificação de Perigos'),
                    (3, 'Avaliação de Riscos'),
                    (4, 'Planejamento e Controle'),
                    (5, 'Monitoramento e Revisão'),
                    (6, 'Comunicação e Cultura')
                ])),
                ('item_texto', models.TextField(help_text='Descrição da tarefa do checklist')),
                ('item_ordem', models.IntegerField(help_text='Ordem do item dentro da etapa')),
                ('concluido', models.BooleanField(default=False)),
                ('data_conclusao', models.DateTimeField(blank=True, null=True)),
                ('responsavel', models.CharField(blank=True, max_length=255)),
                ('prazo', models.DateField(blank=True, null=True)),
                ('observacoes', models.TextField(blank=True)),
                ('automatico', models.BooleanField(default=False, help_text='Item preenchido automaticamente pelo sistema')),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_nr1_items', to='surveys.campaign')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_nr1_items', to='tenants.empresa')),
            ],
            options={
                'verbose_name': 'Item de Checklist NR-1',
                'verbose_name_plural': 'Itens de Checklist NR-1',
                'db_table': 'actions_checklist_nr1_etapa',
                'ordering': ['etapa', 'item_ordem'],
            },
        ),
        migrations.CreateModel(
            name='EvidenciaNR1',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('arquivo', models.FileField(help_text='Upload do arquivo de evidência', upload_to='evidencias_nr1/%Y/%m/')),
                ('nome_original', models.CharField(help_text='Nome original do arquivo', max_length=255)),
                ('tipo', models.CharField(choices=[
                    ('documento', 'Documento (PDF, DOC, DOCX)'),
                    ('imagem', 'Imagem (JPG, PNG)'),
                    ('planilha', 'Planilha (XLS, XLSX, CSV)'),
                    ('apresentacao', 'Apresentação (PPT, PPTX)'),
                    ('email', 'E-mail/Comunicado'),
                    ('ata', 'Ata de Reunião'),
                    ('certificado', 'Certificado/Treinamento'),
                    ('outro', 'Outro')
                ], default='outro', max_length=20)),
                ('tamanho_bytes', models.BigIntegerField(default=0, help_text='Tamanho do arquivo em bytes')),
                ('descricao', models.TextField(blank=True, help_text='Descrição da evidência')),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidencias_nr1', to='surveys.campaign')),
                ('checklist_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidencias', to='actions.checklistnr1etapa')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidencias_nr1', to='tenants.empresa')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evidencias_nr1_uploaded', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Evidência NR-1',
                'verbose_name_plural': 'Evidências NR-1',
                'db_table': 'actions_evidencia_nr1',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='checklistnr1etapa',
            unique_together={('campaign', 'etapa', 'item_ordem')},
        ),
    ]
