import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenants', '0004_empresa_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnonymousReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('protocolo', models.CharField(db_index=True, editable=False, help_text='Código de protocolo anônimo para acompanhamento', max_length=16, unique=True)),
                ('access_token_hash', models.CharField(editable=False, help_text='Hash SHA-256 do token de acesso do denunciante', max_length=64)),
                ('categoria', models.CharField(choices=[('assedio_moral', 'Assédio Moral'), ('assedio_sexual', 'Assédio Sexual'), ('discriminacao', 'Discriminação'), ('seguranca', 'Segurança do Trabalho'), ('etica', 'Violação de Ética'), ('corrupcao', 'Corrupção/Fraude'), ('ambiente', 'Ambiente de Trabalho Hostil'), ('outros', 'Outros')], max_length=30)),
                ('gravidade', models.CharField(choices=[('baixa', 'Baixa'), ('media', 'Média'), ('alta', 'Alta'), ('critica', 'Crítica')], default='media', max_length=10)),
                ('titulo', models.CharField(max_length=255)),
                ('descricao', models.TextField(help_text='Descrição detalhada da denúncia')),
                ('local_ocorrencia', models.CharField(blank=True, help_text="Local genérico da ocorrência (ex: 'escritório', 'fábrica')", max_length=255)),
                ('data_ocorrencia_aproximada', models.CharField(blank=True, help_text="Data aproximada (ex: 'início de março 2026', 'últimas semanas')", max_length=50)),
                ('status', models.CharField(choices=[('aberta', 'Aberta'), ('em_analise', 'Em Análise'), ('investigando', 'Investigando'), ('resolvida', 'Resolvida'), ('arquivada', 'Arquivada')], default='aberta', max_length=15)),
                ('prioridade_rh', models.IntegerField(default=0, help_text='Prioridade definida pelo RH (0=não definida, 1-5)')),
                ('reported_at', models.DateTimeField(help_text='Hora arredondada do reporte (para evitar correlação temporal)')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='denuncias', to='tenants.empresa')),
            ],
            options={
                'verbose_name': 'Denúncia Anônima',
                'verbose_name_plural': 'Denúncias Anônimas',
                'db_table': 'reports_anonymous_report',
                'ordering': ['-reported_at'],
                'indexes': [
                    models.Index(fields=['empresa', 'status'], name='reports_ano_empresa_4f5c6a_idx'),
                    models.Index(fields=['empresa', 'categoria'], name='reports_ano_empresa_8d2e1b_idx'),
                    models.Index(fields=['protocolo'], name='reports_ano_protoco_a1b2c3_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ReportResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mensagem', models.TextField(help_text='Resposta ou atualização do RH')),
                ('novo_status', models.CharField(blank=True, choices=[('aberta', 'Aberta'), ('em_analise', 'Em Análise'), ('investigando', 'Investigando'), ('resolvida', 'Resolvida'), ('arquivada', 'Arquivada')], help_text='Novo status após esta resposta', max_length=15)),
                ('visivel_denunciante', models.BooleanField(default=True, help_text='Se esta resposta é visível para o denunciante')),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respostas_rh', to='reports.anonymousreport')),
                ('respondido_por', models.ForeignKey(help_text='Usuário RH que respondeu (não visível ao denunciante)', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Resposta de Denúncia',
                'verbose_name_plural': 'Respostas de Denúncias',
                'db_table': 'reports_report_response',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReportFollowUp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mensagem', models.TextField(help_text='Informação adicional do denunciante')),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followups', to='reports.anonymousreport')),
            ],
            options={
                'verbose_name': 'Complemento de Denúncia',
                'verbose_name_plural': 'Complementos de Denúncias',
                'db_table': 'reports_report_followup',
                'ordering': ['created_at'],
            },
        ),
    ]
