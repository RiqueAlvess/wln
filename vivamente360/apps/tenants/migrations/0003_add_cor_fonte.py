# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_add_cnae_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='cor_fonte',
            field=models.CharField(
                default='#ffffff',
                help_text='Cor da fonte nos botões e elementos primários',
                max_length=7
            ),
        ),
    ]
