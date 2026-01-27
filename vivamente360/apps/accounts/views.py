from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from services.audit_service import AuditService


class LoginView(auth_views.LoginView):
    template_name = 'auth/login.html'

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if request.user.is_authenticated:
            empresa = None
            if hasattr(request.user, 'profile') and request.user.profile.empresas.exists():
                empresa = request.user.profile.empresas.first()
            AuditService.log(request.user, empresa, 'login', request=request)
        return response


class LogoutView(View):
    def get(self, request):
        empresa = None
        if hasattr(request.user, 'profile') and request.user.profile.empresas.exists():
            empresa = request.user.profile.empresas.first()
        AuditService.log(request.user, empresa, 'logout', request=request)
        logout(request)
        return redirect('accounts:login')
