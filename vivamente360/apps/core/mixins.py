from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        # Superusers têm acesso completo
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'profile'):
            raise PermissionDenied
        if request.user.profile.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class RHRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['rh']


class DashboardAccessMixin(RoleRequiredMixin):
    allowed_roles = ['rh', 'lideranca']

    def get_queryset_filtered(self, queryset):
        """
        Filtra queryset baseado nas permissões do usuário.
        - Superusers: acesso completo
        - RH: filtrado por empresas vinculadas
        - Liderança: filtrado por unidades e setores permitidos
        """
        # Superusers têm acesso completo
        if self.request.user.is_superuser:
            return queryset

        profile = self.request.user.profile

        if profile.role == 'rh':
            return queryset.filter(empresa__in=profile.empresas.all())

        if profile.role == 'lideranca':
            return queryset.filter(
                Q(unidade__in=profile.unidades_permitidas.all()) |
                Q(setor__in=profile.setores_permitidos.all())
            )

        return queryset.none()

    def get_unidades_permitidas(self):
        """
        Retorna as unidades que o usuário tem permissão para visualizar.
        - Superusers e RH: todas as unidades das empresas vinculadas
        - Liderança: apenas unidades vinculadas ao perfil
        """
        from apps.structure.models import Unidade

        if self.request.user.is_superuser:
            return Unidade.objects.all()

        if not hasattr(self.request.user, 'profile'):
            return Unidade.objects.none()

        profile = self.request.user.profile

        if profile.role == 'rh':
            return Unidade.objects.filter(empresa__in=profile.empresas.all())

        if profile.role == 'lideranca':
            return profile.unidades_permitidas.all()

        return Unidade.objects.none()

    def get_setores_permitidos(self):
        """
        Retorna os setores que o usuário tem permissão para visualizar.
        - Superusers e RH: todos os setores das empresas vinculadas
        - Liderança: apenas setores vinculados ao perfil
        """
        from apps.structure.models import Setor

        if self.request.user.is_superuser:
            return Setor.objects.all()

        if not hasattr(self.request.user, 'profile'):
            return Setor.objects.none()

        profile = self.request.user.profile

        if profile.role == 'rh':
            return Setor.objects.filter(unidade__empresa__in=profile.empresas.all())

        if profile.role == 'lideranca':
            return profile.setores_permitidos.all()

        return Setor.objects.none()

    def filter_unidades_by_permission(self, unidades_queryset):
        """
        Filtra um queryset de unidades baseado nas permissões do usuário.
        """
        if self.request.user.is_superuser:
            return unidades_queryset

        if not hasattr(self.request.user, 'profile'):
            return unidades_queryset.none()

        profile = self.request.user.profile

        if profile.role == 'rh':
            return unidades_queryset.filter(empresa__in=profile.empresas.all())

        if profile.role == 'lideranca':
            return unidades_queryset.filter(id__in=profile.unidades_permitidas.all())

        return unidades_queryset.none()

    def filter_setores_by_permission(self, setores_queryset):
        """
        Filtra um queryset de setores baseado nas permissões do usuário.
        """
        if self.request.user.is_superuser:
            return setores_queryset

        if not hasattr(self.request.user, 'profile'):
            return setores_queryset.none()

        profile = self.request.user.profile

        if profile.role == 'rh':
            return setores_queryset.filter(unidade__empresa__in=profile.empresas.all())

        if profile.role == 'lideranca':
            return setores_queryset.filter(id__in=profile.setores_permitidos.all())

        return setores_queryset.none()
