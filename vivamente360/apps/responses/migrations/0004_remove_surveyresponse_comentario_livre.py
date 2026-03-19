from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('responses', '0003_remove_surveyresponse_cargo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='surveyresponse',
            name='comentario_livre',
        ),
    ]
