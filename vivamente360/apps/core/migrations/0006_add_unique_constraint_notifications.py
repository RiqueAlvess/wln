# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_exportedfile_model'),
    ]

    operations = [
        # Primeiro, remover notificações duplicadas existentes
        migrations.RunSQL(
            sql="""
                DELETE FROM core_user_notification
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM core_user_notification
                    WHERE task_id IS NOT NULL
                    GROUP BY user_id, task_id, notification_type
                );
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        # Adicionar constraint de unicidade
        migrations.AddConstraint(
            model_name='usernotification',
            constraint=models.UniqueConstraint(
                fields=['user', 'task', 'notification_type'],
                name='unique_notification_per_task',
                condition=models.Q(task__isnull=False)
            ),
        ),
    ]
