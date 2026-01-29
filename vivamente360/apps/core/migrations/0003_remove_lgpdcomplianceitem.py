# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_lgpdcomplianceitem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lgpdcomplianceitem',
            name='empresa',
        ),
        migrations.DeleteModel(
            name='LGPDComplianceItem',
        ),
    ]
