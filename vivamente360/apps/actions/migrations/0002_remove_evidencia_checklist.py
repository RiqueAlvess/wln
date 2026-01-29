# Generated manually

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='evidencia',
            name='checklist_item',
        ),
        migrations.RemoveField(
            model_name='evidencia',
            name='plano_acao',
        ),
        migrations.RemoveField(
            model_name='evidencia',
            name='campaign',
        ),
        migrations.RemoveField(
            model_name='evidencia',
            name='empresa',
        ),
        migrations.RemoveField(
            model_name='evidencia',
            name='uploaded_by',
        ),
        migrations.DeleteModel(
            name='Evidencia',
        ),
        migrations.RemoveField(
            model_name='checklistetapa',
            name='campaign',
        ),
        migrations.RemoveField(
            model_name='checklistetapa',
            name='empresa',
        ),
        migrations.DeleteModel(
            name='ChecklistEtapa',
        ),
    ]
