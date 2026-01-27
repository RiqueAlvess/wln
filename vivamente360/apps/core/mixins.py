from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            raise PermissionDenied
        if request.user.profile.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']


class RHRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'rh']


class DashboardAccessMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'rh', 'lideranca']

    def get_queryset_filtered(self, queryset):
        profile = self.request.user.profile

        if profile.role == 'admin':
            return queryset

        if profile.role == 'rh':
            return queryset.filter(empresa__in=profile.empresas.all())

        if profile.role == 'lideranca':
            return queryset.filter(
                Q(unidade__in=profile.unidades_permitidas.all()) |
                Q(setor__in=profile.setores_permitidos.all())
            )

        return queryset.none()
