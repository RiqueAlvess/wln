import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
from django.conf import settings
from django.db.models import Avg, Count
from apps.responses.models import SurveyResponse
from apps.structure.models import Setor
from apps.surveys.models import Campaign
from apps.analytics.models import SectorAnalysis
from services.score_service import ScoreService
import logging

logger = logging.getLogger(__name__)


class SectorAnalysisService:
    """
    Serviço para geração de análises individualizadas por setor usando IA (GPT-4o via OpenRouter)
    """

    PROMPT_ANALISE_SETOR = """
Você é um especialista em Saúde Ocupacional e Riscos Psicossociais.
Analise os dados do setor abaixo e gere um relatório estruturado.

## DADOS DO SETOR
- Nome: {setor_nome}
- Empresa: {empresa_nome}
- CNAE: {cnae}
- Total de Respostas: {total_respostas}
- Período: {periodo}

## SCORES POR DIMENSÃO HSE-IT
{scores_formatados}

## COMENTÁRIOS DOS COLABORADORES (Anônimos)
{comentarios}

## FORMATO DE RESPOSTA (OBRIGATÓRIO)
Responda EXATAMENTE neste formato JSON:
```json
{{
  "diagnostico": "Texto de 2-3 parágrafos explicando a situação geral do setor",
  "fatores_contribuintes": [
    "Fator 1 identificado",
    "Fator 2 identificado",
    "Fator 3 identificado"
  ],
  "pontos_atencao": [
    {{
      "dimensao": "Nome da dimensão",
      "nivel": "Crítico|Importante|Moderado",
      "descricao": "Explicação do problema"
    }}
  ],
  "pontos_fortes": [
    {{
      "dimensao": "Nome da dimensão",
      "descricao": "O que está funcionando bem"
    }}
  ],
  "recomendacoes": [
    {{
      "prioridade": 1,
      "acao": "Descrição da ação",
      "prazo": "Curto prazo (30 dias)|Médio prazo (90 dias)|Longo prazo (180 dias)",
      "responsavel_sugerido": "Cargo sugerido",
      "recursos": "Recursos necessários"
    }}
  ],
  "impacto_esperado": "Texto descrevendo o impacto esperado das ações",
  "alertas_sentimento": [
    {{
      "tipo": "Assédio|Sobrecarga|Conflito|Saúde Mental|Outro",
      "evidencia": "Trecho relevante do comentário (anonimizado)",
      "gravidade": "Alta|Média|Baixa",
      "recomendacao_imediata": "Ação sugerida"
    }}
  ]
}}
```

IMPORTANTE:
- Seja objetivo e baseado em dados
- Não invente informações não presentes nos dados
- Destaque situações de risco que exigem ação imediata
- Mantenha o anonimato dos colaboradores
- Foque em soluções práticas e viáveis
"""

    @staticmethod
    def _format_scores(scores_data: Dict) -> str:
        """Formata os scores para inclusão no prompt"""
        formatted = []
        for dimensao, data in scores_data.items():
            score = data.get('score', 0)
            classificacao = data.get('classificacao', 'N/A')
            nivel = data.get('interpretacao', 'N/A')
            formatted.append(f"- {dimensao.replace('_', ' ').title()}: {score:.2f} ({classificacao} - {nivel})")
        return "\n".join(formatted)

    @staticmethod
    def _get_sector_data(setor_id: int, campaign_id: int) -> Dict:
        """Coleta dados do setor para análise"""
        try:
            setor = Setor.objects.select_related('unidade__empresa').get(id=setor_id)
            campaign = Campaign.objects.get(id=campaign_id)

            # Buscar respostas do setor
            respostas = SurveyResponse.objects.filter(
                campaign=campaign,
                setor=setor
            )

            total_respostas = respostas.count()

            if total_respostas == 0:
                return None

            # Calcular scores por dimensão
            all_scores = []
            for resposta in respostas:
                scores = ScoreService.processar_resposta_completa(resposta.respostas)
                all_scores.append(scores)

            # Calcular médias
            scores_medios = {}
            for dimensao in ScoreService.DIMENSOES.keys():
                scores_dimensao = [s[dimensao]['score'] for s in all_scores if dimensao in s]
                if scores_dimensao:
                    score_medio = sum(scores_dimensao) / len(scores_dimensao)
                    risco = ScoreService.classificar_risco(score_medio, dimensao)
                    nivel = ScoreService.calcular_nivel_risco(risco['probabilidade'], 2)

                    scores_medios[dimensao] = {
                        'score': score_medio,
                        **risco,
                        **nivel
                    }

            # Buscar comentários livres
            comentarios = []
            for resposta in respostas:
                if resposta.comentario_livre:
                    comentarios.append(resposta.comentario_livre)

            return {
                'setor': setor,
                'campaign': campaign,
                'empresa': setor.unidade.empresa,
                'total_respostas': total_respostas,
                'scores': scores_medios,
                'comentarios': comentarios
            }

        except (Setor.DoesNotExist, Campaign.DoesNotExist) as e:
            logger.error(f"Erro ao buscar dados do setor: {e}")
            return None

    @classmethod
    def _call_openrouter_api(cls, prompt: str) -> Optional[Dict]:
        """Chama a API do OpenRouter com GPT-4o"""
        if not settings.OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY não configurada")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://vivamente360.com.br",
                "X-Title": "VIVAMENTE 360º - Análise de Setor"
            }

            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000,
                "response_format": {"type": "json_object"}
            }

            response = requests.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            # Extrair conteúdo da resposta
            content = result['choices'][0]['message']['content']

            # Parse JSON
            # Remove markdown code blocks se existirem
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao chamar OpenRouter API: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar resposta JSON: {e}")
            return None

    @classmethod
    def gerar_analise(cls, setor_id: int, campaign_id: int, force_regenerate: bool = False) -> Optional[SectorAnalysis]:
        """
        Gera análise completa do setor usando IA e salva no banco de dados

        Args:
            setor_id: ID do setor
            campaign_id: ID da campanha
            force_regenerate: Se True, regenera mesmo que já exista

        Returns:
            SectorAnalysis object ou None em caso de erro
        """
        try:
            setor = Setor.objects.select_related('unidade__empresa').get(id=setor_id)
            campaign = Campaign.objects.get(id=campaign_id)

            # Verificar se já existe análise
            if not force_regenerate:
                existing = SectorAnalysis.objects.filter(
                    setor=setor,
                    campaign=campaign,
                    status='completed'
                ).first()
                if existing:
                    logger.info(f"Análise já existe para setor {setor_id} e campanha {campaign_id}")
                    return existing

            # Criar ou atualizar registro
            analysis, created = SectorAnalysis.objects.get_or_create(
                setor=setor,
                campaign=campaign,
                defaults={
                    'empresa': setor.unidade.empresa,
                    'status': 'processing'
                }
            )

            if not created:
                analysis.status = 'processing'
                analysis.save()

            # Coletar dados
            data = cls._get_sector_data(setor_id, campaign_id)
            if not data:
                analysis.status = 'failed'
                analysis.error_message = 'Não foram encontrados dados suficientes para análise'
                analysis.save()
                return None

            # Formatar scores
            scores_formatados = cls._format_scores(data['scores'])

            # Formatar comentários
            comentarios_texto = "\n".join([f"- {c}" for c in data['comentarios']]) if data['comentarios'] else "Nenhum comentário registrado"

            # Formatar período
            periodo = f"{data['campaign'].data_inicio.strftime('%d/%m/%Y')} - {data['campaign'].data_fim.strftime('%d/%m/%Y')}"

            # Montar prompt
            prompt = cls.PROMPT_ANALISE_SETOR.format(
                setor_nome=data['setor'].nome,
                empresa_nome=data['empresa'].nome,
                cnae=getattr(data['empresa'], 'cnae', 'N/A'),
                total_respostas=data['total_respostas'],
                periodo=periodo,
                scores_formatados=scores_formatados,
                comentarios=comentarios_texto
            )

            # Chamar API
            resultado = cls._call_openrouter_api(prompt)

            if not resultado:
                analysis.status = 'failed'
                analysis.error_message = 'Erro ao chamar API do OpenRouter'
                analysis.save()
                return None

            # Salvar resultados
            analysis.diagnostico = resultado.get('diagnostico', '')
            analysis.fatores_contribuintes = resultado.get('fatores_contribuintes', [])
            analysis.pontos_atencao = resultado.get('pontos_atencao', [])
            analysis.pontos_fortes = resultado.get('pontos_fortes', [])
            analysis.recomendacoes = resultado.get('recomendacoes', [])
            analysis.impacto_esperado = resultado.get('impacto_esperado', '')
            analysis.alertas_sentimento = resultado.get('alertas_sentimento', [])
            analysis.total_respostas = data['total_respostas']
            analysis.scores = data['scores']
            analysis.status = 'completed'
            analysis.error_message = ''
            analysis.save()

            logger.info(f"Análise gerada com sucesso para setor {setor_id} e campanha {campaign_id}")
            return analysis

        except (Setor.DoesNotExist, Campaign.DoesNotExist) as e:
            logger.error(f"Erro ao buscar setor ou campanha: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao gerar análise: {e}")
            if 'analysis' in locals():
                analysis.status = 'failed'
                analysis.error_message = str(e)
                analysis.save()
            return None

    @staticmethod
    def get_analise(setor_id: int, campaign_id: int) -> Optional[SectorAnalysis]:
        """
        Recupera análise existente do banco de dados

        Args:
            setor_id: ID do setor
            campaign_id: ID da campanha

        Returns:
            SectorAnalysis object ou None se não existir
        """
        try:
            return SectorAnalysis.objects.filter(
                setor_id=setor_id,
                campaign_id=campaign_id,
                status='completed'
            ).first()
        except Exception as e:
            logger.error(f"Erro ao recuperar análise: {e}")
            return None
