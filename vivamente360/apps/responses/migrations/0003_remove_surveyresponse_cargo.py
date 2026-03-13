"""
Remove cargo FK from SurveyResponse to strengthen anonymity.

Having cargo in the response allows cross-referencing with SurveyInvitation
(which also has cargo) to de-anonymize responses, especially in small teams
with unique positions. This breaks the blind-drop pattern.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('responses', '0002_add_sentiment_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='surveyresponse',
            name='cargo',
        ),
    ]
