from apps.accounts.models import AuditLog
from apps.core.utils import get_client_ip


class AuditService:
    @staticmethod
    def log(user, empresa, acao: str, descricao: str = '', request=None):
        AuditLog.objects.create(
            user=user,
            empresa=empresa,
            acao=acao,
            descricao=descricao,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
        )
