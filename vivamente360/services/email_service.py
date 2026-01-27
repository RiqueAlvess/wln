from abc import ABC, abstractmethod
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailServiceBase(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> bool:
        pass

    @abstractmethod
    def send_bulk(self, emails: list) -> dict:
        pass


class ResendEmailService(EmailServiceBase):
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.DEFAULT_FROM_EMAIL

    def send(self, to: str, subject: str, html_body: str) -> bool:
        try:
            import resend
            resend.api_key = self.api_key

            resend.Emails.send({
                "from": self.from_email,
                "to": to,
                "subject": subject,
                "html": html_body,
            })
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False

    def send_bulk(self, emails: list) -> dict:
        success = 0
        failed = 0
        for email in emails:
            if self.send(email['to'], email['subject'], email['html']):
                success += 1
            else:
                failed += 1
        return {"success": success, "failed": failed}


def get_email_service() -> EmailServiceBase:
    provider = settings.EMAIL_PROVIDER
    if provider == 'resend':
        return ResendEmailService()
    raise ValueError(f"Provider {provider} não suportado")
