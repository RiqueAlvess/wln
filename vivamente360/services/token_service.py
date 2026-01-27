import uuid
from datetime import timedelta
from django.utils import timezone


class TokenService:
    TOKEN_EXPIRY_HOURS = 48

    @staticmethod
    def generate_token():
        return uuid.uuid4()

    @staticmethod
    def get_expiry():
        return timezone.now() + timedelta(hours=TokenService.TOKEN_EXPIRY_HOURS)

    @staticmethod
    def validate_token(invitation):
        if invitation.status == 'used':
            return False, "Este link já foi utilizado."
        if invitation.expires_at < timezone.now():
            return False, "Este link expirou."
        return True, ""

    @staticmethod
    def invalidate_token(invitation):
        invitation.status = 'used'
        invitation.used_at = timezone.now()
        invitation.save(update_fields=['status', 'used_at'])
