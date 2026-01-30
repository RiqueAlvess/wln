# Generated manually for rich text editor fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0003_add_checklist_nr1_evidencia_nr1'),
    ]

    operations = [
        migrations.AddField(
            model_name='planoacao',
            name='conteudo_estruturado',
            field=models.JSONField(
                blank=True,
                help_text='Conteúdo do editor TipTap em formato JSON',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='planoacao',
            name='conteudo_html',
            field=models.TextField(
                blank=True,
                default='',
                help_text='HTML renderizado do plano de ação para exportação'
            ),
        ),
    ]
