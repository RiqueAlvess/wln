from django.db import transaction
from django.utils import timezone
from apps.core.models import TaskQueue
from apps.invitations.models import SurveyInvitation
from services.email_service import get_email_service


def process_email_queue():
    with transaction.atomic():
        task = TaskQueue.objects.select_for_update(skip_locked=True).filter(
            task_type='send_email',
            status='pending'
        ).first()

        if not task:
            return

        task.status = 'processing'
        task.started_at = timezone.now()
        task.attempts += 1
        task.save()

    try:
        email_service = get_email_service()
        success = email_service.send(
            to=task.payload['to'],
            subject=task.payload['subject'],
            html_body=task.payload['html']
        )

        if success:
            task.status = 'completed'
            task.completed_at = timezone.now()

            SurveyInvitation.objects.filter(
                id=task.payload['invitation_id']
            ).update(status='sent', sent_at=timezone.now())
        else:
            raise Exception("Falha no envio")

    except Exception as e:
        task.error_message = str(e)
        if task.attempts >= task.max_attempts:
            task.status = 'failed'
        else:
            task.status = 'pending'

    task.save()
