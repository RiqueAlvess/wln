from rest_framework import serializers
from .models import PlanoAcao, ChecklistNR1Etapa, EvidenciaNR1
from apps.surveys.models import Campaign
from apps.tenants.models import Empresa


class PlanoAcaoSerializer(serializers.ModelSerializer):
    dimensao_nome = serializers.CharField(source='dimensao.nome', read_only=True)
    campaign_nome = serializers.CharField(source='campaign.nome', read_only=True)
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)

    class Meta:
        model = PlanoAcao
        fields = [
            'id', 'empresa', 'empresa_nome', 'campaign', 'campaign_nome',
            'dimensao', 'dimensao_nome', 'nivel_risco', 'descricao_risco',
            'acao_proposta', 'responsavel', 'prazo', 'recursos_necessarios',
            'indicadores', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EvidenciaNR1Serializer(serializers.ModelSerializer):
    uploaded_by_nome = serializers.SerializerMethodField()
    tamanho_formatado = serializers.CharField(source='get_tamanho_formatado', read_only=True)
    extensao = serializers.CharField(read_only=True)
    arquivo_url = serializers.SerializerMethodField()

    class Meta:
        model = EvidenciaNR1
        fields = [
            'id', 'checklist_item', 'campaign', 'empresa',
            'arquivo', 'arquivo_url', 'nome_original', 'tipo',
            'tamanho_bytes', 'tamanho_formatado', 'extensao',
            'descricao', 'uploaded_by', 'uploaded_by_nome',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'tamanho_bytes', 'nome_original']

    def get_uploaded_by_nome(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return "Sistema"

    def get_arquivo_url(self, obj):
        if obj.arquivo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.arquivo.url)
            return obj.arquivo.url
        return None

    def create(self, validated_data):
        # Extrair informações do arquivo
        arquivo = validated_data.get('arquivo')
        if arquivo:
            validated_data['nome_original'] = arquivo.name
            validated_data['tamanho_bytes'] = arquivo.size
        return super().create(validated_data)


class ChecklistNR1EtapaSerializer(serializers.ModelSerializer):
    etapa_display = serializers.CharField(source='get_etapa_display', read_only=True)
    progresso_etapa = serializers.SerializerMethodField()
    evidencias = EvidenciaNR1Serializer(many=True, read_only=True)
    evidencias_count = serializers.SerializerMethodField()

    class Meta:
        model = ChecklistNR1Etapa
        fields = [
            'id', 'campaign', 'empresa', 'etapa', 'etapa_display',
            'item_texto', 'item_ordem', 'concluido', 'data_conclusao',
            'responsavel', 'prazo', 'observacoes', 'automatico',
            'progresso_etapa', 'evidencias', 'evidencias_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_progresso_etapa(self, obj):
        return obj.get_progresso_etapa()

    def get_evidencias_count(self, obj):
        return obj.evidencias.count()


class ChecklistNR1ResumoSerializer(serializers.Serializer):
    """
    Serializer para resumo geral do checklist de uma campanha
    """
    campaign_id = serializers.IntegerField()
    campaign_nome = serializers.CharField()
    total_itens = serializers.IntegerField()
    itens_concluidos = serializers.IntegerField()
    progresso_geral = serializers.FloatField()

    etapas = serializers.ListField(
        child=serializers.DictField()
    )

    ultima_atualizacao = serializers.DateTimeField()


class ChecklistNR1ExportSerializer(serializers.Serializer):
    """
    Serializer para exportação completa do checklist
    """
    campaign = serializers.DictField()
    empresa = serializers.DictField()
    progresso_geral = serializers.FloatField()
    etapas = serializers.ListField(
        child=serializers.DictField()
    )
    gerado_em = serializers.DateTimeField()
