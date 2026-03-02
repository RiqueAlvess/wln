# Generated manually - adds choices and default to PlanoAcao.nivel_risco

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions", "0005_alter_planoacao_conteudo_html"),
    ]

    operations = [
        migrations.AlterField(
            model_name="planoacao",
            name="nivel_risco",
            field=models.CharField(
                choices=[
                    ("aceitavel", "Aceitável"),
                    ("moderado", "Moderado"),
                    ("importante", "Importante"),
                    ("critico", "Crítico"),
                ],
                default="moderado",
                max_length=20,
            ),
        ),
    ]
