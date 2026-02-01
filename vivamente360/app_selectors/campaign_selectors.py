from apps.surveys.models import Campaign
from django.db.models import Q


class CampaignSelectors:
    @staticmethod
    def get_user_campaigns(user):
        # Superusers têm acesso a todas as campanhas
        if user.is_superuser:
            return Campaign.objects.all()

        if not hasattr(user, 'profile'):
            return Campaign.objects.none()

        profile = user.profile

        if profile.role == 'rh':
            return Campaign.objects.filter(empresa__in=profile.empresas.all())

        if profile.role == 'lideranca':
            return Campaign.objects.filter(
                Q(empresa__unidades__in=profile.unidades_permitidas.all()) |
                Q(empresa__unidades__setores__in=profile.setores_permitidos.all())
            ).distinct()

        return Campaign.objects.none()

    @staticmethod
    def get_active_campaigns():
        return Campaign.objects.filter(status='active')
