"""
Serviço de Análise de Comentários com IA para Riscos Psicossociais

Utiliza GPT-4o via OpenRouter para:
- Análise de sentimento
- Identificação de fatores de risco NR-1
- Detecção de alertas críticos
- Sugestão de ajustes de probabilidade
"""

import json
from typing import Dict, List, Optional
from apps.structure.models import Setor
from apps.responses.models import SurveyResponse
from services.ai_service import AIService
from services.ai_prompts import PROMPT_ANALISE_COMENTARIOS_RISCO
from app_selectors.dashboard_selectors import DashboardSelectors


class AICommentAnalysisService:
    """Serviço de análise de comentários usando IA (GPT-4o via OpenRouter)"""

    def __init__(self):
        self.ai_service = AIService()

    def analisar_comentarios_setor(
        self,
        campaign,
        setor: Setor,
        comentarios: Optional[List[str]] = None
    ) -> Dict:
        """
        Analisa comentários de um setor específico.

        Args:
            campaign: Objeto Campaign
            setor: Objeto Setor
            comentarios: Lista de strings com os comentários (opcional, busca do DB se não fornecido)

        Returns:
            Dict com análise estruturada
        """
        # Buscar comentários do banco se não fornecidos
        if comentarios is None:
            comentarios = list(
                SurveyResponse.objects.filter(
                    campaign=campaign,
                    setor=setor,
                    comentario_livre__isnull=False
                ).exclude(
                    comentario_livre=''
                ).values_list('comentario_livre', flat=True)
            )

        if not comentarios:
            return {
                'erro': 'Nenhum comentário disponível para análise',
                'total_comentarios': 0
            }

        # Preparar contexto
        empresa = campaign.empresa
        cnae = getattr(empresa, 'cnae', 'N/A')
        cnae_descricao = getattr(empresa, 'cnae_descricao', 'Não especificado')

        # Calcular score médio do setor (média de todas as dimensões)
        from services.score_service import ScoreService
        scores_dimensoes = {}
        respostas_setor = SurveyResponse.objects.filter(
            campaign=campaign,
            setor=setor
        )

        if respostas_setor.exists():
            # Calcular média dos scores de todas as respostas
            from apps.surveys.models import Dimensao
            dimensoes = Dimensao.objects.filter(ativo=True)

            for dimensao in dimensoes:
                scores_lista = []
                for resposta in respostas_setor:
                    score = ScoreService.calcular_score_dimensao(
                        resposta.respostas,
                        dimensao.codigo
                    )
                    if score is not None:
                        scores_lista.append(score)

                if scores_lista:
                    scores_dimensoes[dimensao.codigo] = sum(scores_lista) / len(scores_lista)

            score_medio = sum(scores_dimensoes.values()) / len(scores_dimensoes) if scores_dimensoes else 2.0
        else:
            score_medio = 2.0

        # Formatar comentários (anonimizados, numerados)
        comentarios_formatados = "\n\n".join([
            f"[Colaborador {i+1}]: {c}"
            for i, c in enumerate(comentarios)
        ])

        # Montar prompt
        prompt = PROMPT_ANALISE_COMENTARIOS_RISCO.format(
            comentarios_formatados=comentarios_formatados,
            empresa_nome=empresa.nome,
            cnae=cnae,
            cnae_descricao=cnae_descricao,
            setor_nome=setor.nome,
            total_comentarios=len(comentarios),
            score_medio=f"{score_medio:.2f}"
        )

        # Chamar IA
        resultado = self.ai_service.completar(
            prompt,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )

        if resultado['success']:
            try:
                analise = self._processar_resultado_ia(resultado['content'])
                analise['total_comentarios'] = len(comentarios)
                analise['setor'] = setor
                analise['campaign'] = campaign
                return analise
            except Exception as e:
                return {
                    'erro': f'Erro ao processar resposta da IA: {str(e)}',
                    'raw_content': resultado.get('content', '')
                }
        else:
            return {
                'erro': resultado.get('error', 'Falha na análise'),
                'total_comentarios': len(comentarios)
            }

    def _processar_resultado_ia(self, conteudo) -> Dict:
        """Processa e valida resultado da IA"""

        # Se já for dict, usar diretamente
        if isinstance(conteudo, dict):
            analise = conteudo
        else:
            # Tentar parsear JSON
            try:
                analise = json.loads(conteudo)
            except json.JSONDecodeError:
                # Tentar extrair JSON de markdown
                if '```json' in conteudo:
                    json_str = conteudo.split('```json')[1].split('```')[0].strip()
                    analise = json.loads(json_str)
                else:
                    raise ValueError("Resposta da IA não está em formato JSON válido")

        # Validar estrutura mínima
        campos_obrigatorios = [
            'resumo_geral',
            'fatores_identificados',
            'alertas_criticos'
        ]

        for campo in campos_obrigatorios:
            if campo not in analise:
                if campo == 'resumo_geral':
                    analise[campo] = {
                        'sentimento_predominante': 'Neutro',
                        'score_sentimento': 0.0,
                        'nivel_preocupacao': 'Médio'
                    }
                else:
                    analise[campo] = []

        # Garantir campos opcionais
        if 'temas_recorrentes' not in analise:
            analise['temas_recorrentes'] = []
        if 'pontos_positivos' not in analise:
            analise['pontos_positivos'] = []
        if 'recomendacoes_gerais' not in analise:
            analise['recomendacoes_gerais'] = []

        return analise

    def ajustar_probabilidade_com_ia(
        self,
        probabilidade_base: int,
        ajuste_ia: int
    ) -> int:
        """
        Ajusta a probabilidade baseado na análise de comentários.

        Args:
            probabilidade_base: Probabilidade calculada pelo algoritmo (1-5)
            ajuste_ia: Ajuste sugerido pela IA (-1, 0, +1)

        Returns:
            Probabilidade ajustada (1-5)
        """
        # Validar ajuste
        if ajuste_ia not in [-1, 0, 1]:
            ajuste_ia = 0

        probabilidade_ajustada = probabilidade_base + ajuste_ia

        # Garantir limites
        return max(1, min(5, probabilidade_ajustada))

    def extrair_alertas_criticos(
        self,
        analises_setores: Dict[int, Dict]
    ) -> List[Dict]:
        """
        Extrai todos os alertas críticos de múltiplas análises de setores.

        Args:
            analises_setores: Dict com {setor_id: analise_dict}

        Returns:
            Lista de alertas ordenados por gravidade
        """
        alertas = []

        for setor_id, analise in analises_setores.items():
            for alerta in analise.get('alertas_criticos', []):
                alerta_completo = alerta.copy()
                alerta_completo['setor_id'] = setor_id
                alerta_completo['setor'] = analise.get('setor')
                alertas.append(alerta_completo)

        # Ordenar por gravidade (Crítica antes de Alta)
        alertas.sort(
            key=lambda x: 0 if x.get('gravidade') == 'Crítica' else 1
        )

        return alertas

    def consolidar_fatores_identificados(
        self,
        analises_setores: Dict[int, Dict]
    ) -> Dict[str, Dict]:
        """
        Consolida fatores identificados de múltiplos setores.

        Args:
            analises_setores: Dict com {setor_id: analise_dict}

        Returns:
            Dict com fatores consolidados por código
        """
        fatores_consolidados = {}

        for setor_id, analise in analises_setores.items():
            for fator in analise.get('fatores_identificados', []):
                codigo = fator.get('codigo_fator')
                if not codigo:
                    continue

                if codigo not in fatores_consolidados:
                    fatores_consolidados[codigo] = {
                        'codigo': codigo,
                        'nome': fator.get('nome_fator', ''),
                        'total_mencoes': 0,
                        'setores_afetados': [],
                        'evidencias_totais': [],
                        'ajustes_probabilidade': []
                    }

                # Acumular dados
                fatores_consolidados[codigo]['total_mencoes'] += fator.get('frequencia_mencoes', 0)
                fatores_consolidados[codigo]['setores_afetados'].append({
                    'setor_id': setor_id,
                    'setor': analise.get('setor'),
                    'mencoes': fator.get('frequencia_mencoes', 0)
                })
                fatores_consolidados[codigo]['evidencias_totais'].extend(
                    fator.get('evidencias', [])
                )
                if 'ajuste_probabilidade' in fator:
                    fatores_consolidados[codigo]['ajustes_probabilidade'].append(
                        fator['ajuste_probabilidade']
                    )

        # Calcular ajuste médio para cada fator
        for codigo, dados in fatores_consolidados.items():
            if dados['ajustes_probabilidade']:
                dados['ajuste_medio'] = round(
                    sum(dados['ajustes_probabilidade']) / len(dados['ajustes_probabilidade'])
                )
            else:
                dados['ajuste_medio'] = 0

        return fatores_consolidados
