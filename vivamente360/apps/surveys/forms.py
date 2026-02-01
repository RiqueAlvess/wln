from django import forms
from apps.surveys.models import Campaign


class CampaignForm(forms.ModelForm):
    """
    Formulário para criação e edição de campanhas.
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir status inicial como 'draft'
        if not self.instance.pk:
            self.fields['status'].initial = 'draft'
