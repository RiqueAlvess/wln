# Generated migration for Artigo model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Artigo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('titulo', models.CharField(help_text='Título principal do artigo', max_length=255, verbose_name='Título')),
                ('slug', models.SlugField(help_text='URL amigável (gerado automaticamente do título)', max_length=255, unique=True, verbose_name='Slug')),
                ('resumo', models.TextField(help_text='Texto exibido no card de prévia (máx. 500 caracteres)', max_length=500, verbose_name='Resumo')),
                ('conteudo', models.TextField(help_text='Conteúdo completo do artigo (suporta Markdown)', verbose_name='Conteúdo')),
                ('imagem_capa', models.ImageField(blank=True, help_text='Imagem principal do artigo', null=True, upload_to='artigos/%Y/%m/', verbose_name='Imagem de Capa')),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('published', 'Publicado'), ('archived', 'Arquivado')], default='draft', help_text='Status de publicação do artigo', max_length=10, verbose_name='Status')),
                ('publicado_em', models.DateTimeField(blank=True, help_text='Data e hora de publicação', null=True, verbose_name='Publicado em')),
                ('destaque', models.BooleanField(default=False, help_text='Exibir artigo em destaque na página principal', verbose_name='Em Destaque')),
                ('categoria', models.CharField(choices=[('nr1', 'NR-1 e Compliance'), ('saude', 'Saúde Mental'), ('gestao', 'Gestão de Pessoas'), ('dicas', 'Dicas Práticas'), ('casos', 'Casos de Sucesso'), ('novidades', 'Novidades do Sistema')], help_text='Categoria do artigo', max_length=20, verbose_name='Categoria')),
                ('visualizacoes', models.PositiveIntegerField(default=0, help_text='Número de visualizações do artigo', verbose_name='Visualizações')),
                ('autor', models.ForeignKey(help_text='Usuário que criou o artigo', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='artigos', to=settings.AUTH_USER_MODEL, verbose_name='Autor')),
            ],
            options={
                'verbose_name': 'Artigo',
                'verbose_name_plural': 'Artigos',
                'ordering': ['-publicado_em', '-created_at'],
                'indexes': [
                    models.Index(fields=['-publicado_em'], name='articles_ar_publicad_idx'),
                    models.Index(fields=['status', 'categoria'], name='articles_ar_status_cat_idx'),
                    models.Index(fields=['destaque', 'status'], name='articles_ar_destaque_status_idx'),
                ],
            },
        ),
    ]
