from apps.tenants.models import Empresa


def branding(request):
    """
    Context processor para disponibilizar dados de branding em todos os templates.
    """
    empresa = None

    if request.user.is_authenticated:
        # Superusers veem a primeira empresa ativa
        if request.user.is_superuser:
            empresa = Empresa.objects.filter(ativo=True).first()
        elif hasattr(request.user, 'profile'):
            profile = request.user.profile

            if profile.role == 'rh':
                empresa = profile.empresas.filter(ativo=True).first()
            elif profile.role == 'lideranca':
                if profile.unidades_permitidas.exists():
                    empresa = profile.unidades_permitidas.first().empresa
                elif profile.setores_permitidos.exists():
                    empresa = profile.setores_permitidos.first().unidade.empresa

    if not empresa:
        empresa = Empresa.objects.filter(ativo=True).first()

    if empresa:
        return {
            'empresa': empresa,
            'branding': {
                'nome_app': empresa.nome_app,
                'logo_url': empresa.logo_url,
                'favicon_url': empresa.favicon_url,
                'cor_primaria': empresa.cor_primaria,
                'cor_secundaria': empresa.cor_secundaria,
                'cor_fonte': empresa.cor_fonte,
            }
        }

    return {
        'empresa': None,
        'branding': {
            'nome_app': 'VIVAMENTE 360º',
            'logo_url': '',
            'favicon_url': '',
            'cor_primaria': '#0d6efd',
            'cor_secundaria': '#6c757d',
            'cor_fonte': '#ffffff',
        }
    }
