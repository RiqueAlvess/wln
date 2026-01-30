from django import forms
from .models import PlanoAcao
from apps.surveys.models import Dimensao


class PlanoAcaoForm(forms.ModelForm):
    """
    Formulário para criação e edição de Plano de Ação com editor rico
    """

    class Meta:
        model = PlanoAcao
        fields = [
            'dimensao',
            'nivel_risco',
            'responsavel',
            'prazo',
            'status',
            'descricao_risco',
            'acao_proposta',
            'recursos_necessarios',
            'indicadores',
            'conteudo_estruturado',
            'conteudo_html',
        ]
        widgets = {
            'dimensao': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'nivel_risco': forms.Select(
                choices=[
                    ('', 'Selecione...'),
                    ('BAIXO', 'Baixo'),
                    ('MODERADO', 'Moderado'),
                    ('ALTO', 'Alto'),
                    ('CRÍTICO', 'Crítico'),
                ],
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável',
                'required': True
            }),
            'prazo': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descricao_risco': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do risco identificado (campo legado)'
            }),
            'acao_proposta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ação proposta para mitigar o risco (campo legado)'
            }),
            'recursos_necessarios': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recursos necessários (campo legado)'
            }),
            'indicadores': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Indicadores de acompanhamento (campo legado)'
            }),
            'conteudo_estruturado': forms.HiddenInput(),
            'conteudo_html': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        campaign = kwargs.pop('campaign', None)
        super().__init__(*args, **kwargs)

        # Filtrar dimensões pela campanha
        if campaign:
            # Obter dimensões do questionário da campanha
            if hasattr(campaign, 'questionario'):
                dimensoes_ids = campaign.questionario.perguntas.values_list(
                    'dimensao_id', flat=True
                ).distinct()
                self.fields['dimensao'].queryset = Dimensao.objects.filter(
                    id__in=dimensoes_ids
                )
            else:
                self.fields['dimensao'].queryset = Dimensao.objects.all()

        # Tornar campos legados opcionais se houver conteúdo estruturado
        if self.instance and self.instance.conteudo_estruturado:
            self.fields['descricao_risco'].required = False
            self.fields['acao_proposta'].required = False

    def clean(self):
        cleaned_data = super().clean()
        conteudo_estruturado = cleaned_data.get('conteudo_estruturado')
        descricao_risco = cleaned_data.get('descricao_risco')
        acao_proposta = cleaned_data.get('acao_proposta')

        # Validar que ao menos um tipo de conteúdo está presente
        if not conteudo_estruturado and not (descricao_risco and acao_proposta):
            raise forms.ValidationError(
                'É necessário preencher o editor de plano de ação ou os campos legados '
                '(Descrição do Risco e Ação Proposta).'
            )

        return cleaned_data
