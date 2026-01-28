from django import forms
from .models import Evidencia


class EvidenciaForm(forms.ModelForm):
    TIPO_CHOICES = [
        ('documento', 'Documento'),
        ('foto', 'Foto'),
        ('certificado', 'Certificado'),
    ]

    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Evidencia
        fields = ['arquivo', 'descricao', 'tipo', 'checklist_item', 'plano_acao']
        widgets = {
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf,.doc,.docx,.xls,.xlsx'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva a evidência...'
            }),
            'checklist_item': forms.Select(attrs={'class': 'form-select'}),
            'plano_acao': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'arquivo': 'Arquivo',
            'descricao': 'Descrição',
            'tipo': 'Tipo de Evidência',
            'checklist_item': 'Item do Checklist (opcional)',
            'plano_acao': 'Plano de Ação (opcional)',
        }
