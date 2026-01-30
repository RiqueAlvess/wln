# Generated manually for psychosocial risk assessment module

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaFatorRisco',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('codigo', models.CharField(max_length=20, unique=True)),
                ('nome', models.CharField(max_length=100)),
                ('descricao', models.TextField()),
                ('icone', models.CharField(default='bi-exclamation-triangle', max_length=50)),
                ('ordem', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Categoria de Fator de Risco',
                'verbose_name_plural': 'Categorias de Fatores de Risco',
                'db_table': 'surveys_categoria_fator_risco',
                'ordering': ['ordem'],
            },
        ),
        migrations.CreateModel(
            name='FatorRisco',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('codigo', models.CharField(max_length=50, unique=True)),
                ('nome', models.CharField(max_length=255)),
                ('descricao', models.TextField()),
                ('exemplos', models.TextField(help_text='Exemplos práticos deste fator de risco')),
                ('severidade_base', models.IntegerField(default=3, help_text='1=Leve, 2=Moderado, 3=Significativo, 4=Grave, 5=Catastrófico')),
                ('consequencias', models.JSONField(default=list, help_text='Lista de consequências possíveis (saude_mental, saude_fisica, acidentes)')),
                ('ativo', models.BooleanField(default=True)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fatores', to='surveys.categoriafatorrisco')),
                ('dimensoes_hse', models.ManyToManyField(help_text='Dimensões HSE-IT relacionadas a este fator', related_name='fatores_risco', to='surveys.dimensao')),
            ],
            options={
                'verbose_name': 'Fator de Risco Psicossocial',
                'verbose_name_plural': 'Fatores de Risco Psicossociais',
                'db_table': 'surveys_fator_risco',
                'ordering': ['categoria', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='SeveridadePorCNAE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cnae_secao', models.CharField(help_text='Seção CNAE (A-U)', max_length=1)),
                ('cnae_divisao', models.CharField(blank=True, help_text='Divisão CNAE (01-99) - Opcional para especificar melhor', max_length=2)),
                ('severidade_ajustada', models.IntegerField(help_text='Severidade específica para este CNAE (1-5)')),
                ('justificativa', models.TextField(help_text='Por que este CNAE tem severidade diferente da base')),
                ('fator_risco', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='severidades_cnae', to='surveys.fatorrisco')),
            ],
            options={
                'verbose_name': 'Severidade por CNAE',
                'verbose_name_plural': 'Severidades por CNAE',
                'db_table': 'surveys_severidade_cnae',
                'unique_together': {('fator_risco', 'cnae_secao', 'cnae_divisao')},
            },
        ),
    ]
