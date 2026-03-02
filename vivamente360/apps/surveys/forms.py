from django import forms
from apps.surveys.models import Campaign
from apps.tenants.models import Empresa


class CampaignForm(forms.ModelForm):
    """
    Formulário para criação e edição de campanhas.
    Aceita user=None para filtrar empresas pelo tenant do usuário logado.
    """

    class Meta:
        model = Campaign
        fields = ['nome', 'descricao', 'empresa', 'data_inicio', 'data_fim', 'status']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ex: Avaliação Anual 2024'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Descreva os objetivos e contexto desta campanha...'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': 'required'
            }),
            'data_inicio': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'data_fim': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'status': forms.HiddenInput()
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir status inicial como 'draft'
        if not self.instance.pk:
            self.fields['status'].initial = 'draft'

        # Filtrar empresas pelo tenant do usuário — evita exposição cross-tenant
        if user is not None:
            if user.is_superuser:
                empresas = Empresa.objects.all()
            elif hasattr(user, 'profile'):
                empresas = user.profile.empresas.all()
            else:
                empresas = Empresa.objects.none()

            self.fields['empresa'].queryset = empresas

            # Se usuário tem apenas uma empresa, pré-seleciona e oculta o campo
            if empresas.count() == 1:
                self.fields['empresa'].initial = empresas.first()
                self.fields['empresa'].widget = forms.HiddenInput()
