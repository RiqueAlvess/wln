# Generated manually for adding CNAE fields to Empresa

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='cnae',
            field=models.CharField(blank=True, help_text='Código CNAE principal da empresa (ex: 62.01-5)', max_length=10),
        ),
        migrations.AddField(
            model_name='empresa',
            name='cnae_descricao',
            field=models.CharField(blank=True, help_text='Descrição da atividade CNAE', max_length=255),
        ),
    ]
