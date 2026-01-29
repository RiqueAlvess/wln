from django.views.generic import TemplateView
from django.shortcuts import redirect, render
from django.conf import settings


class HomeView(TemplateView):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('analytics:dashboard')
        return redirect('accounts:login')


# Views para teste de páginas de erro (apenas em desenvolvimento)
def test_404(request):
    """View para testar página 404"""
    if not settings.DEBUG:
        return redirect('core:home')
    return render(request, '404.html', status=404)


def test_500(request):
    """View para testar página 500"""
    if not settings.DEBUG:
        return redirect('core:home')
    return render(request, '500.html', status=500)


def test_403(request):
    """View para testar página 403"""
    if not settings.DEBUG:
        return redirect('core:home')
    return render(request, '403.html', status=403)


def test_400(request):
    """View para testar página 400"""
    if not settings.DEBUG:
        return redirect('core:home')
    return render(request, '400.html', status=400)
