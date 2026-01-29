import json
import requests
from typing import Dict, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SentimentService:
    """
    Serviço para análise de sentimento de comentários livres usando IA (GPT-4o via OpenRouter)
    """

    PROMPT_ANALISE_SENTIMENTO = """
Analise o comentário abaixo de um colaborador sobre seu ambiente de trabalho.

COMENTÁRIO:
"{comentario}"

RESPONDA EM JSON:
```json
{{
  "score": 0.0,
  "sentimento_geral": "Positivo|Neutro|Negativo|Misto",
  "categorias": ["Sobrecarga", "Reconhecimento", "Liderança", "Colegas", "Ambiente", "Carreira", "Saúde"],
  "pontos_destaque": [
    {{
      "tipo": "Preocupação|Elogio|Sugestão|Desabafo",
      "texto_relevante": "trecho do comentário",
      "gravidade": "Alta|Média|Baixa|N/A"
    }}
  ],
  "alertas": [
    {{
      "tipo": "Assédio|Burnout|Conflito Grave|Saúde Mental|Discriminação",
      "evidencia": "trecho que indica o alerta",
      "acao_recomendada": "O que a empresa deve fazer"
    }}
  ],
  "temas_principais": ["tema1", "tema2"]
}}
```

IMPORTANTE:
- O campo "score" deve ser um número entre -1.0 (muito negativo) e 1.0 (muito positivo)
- Identifique situações de risco que exigem atenção imediata
- Destaque menções a assédio, burnout, discriminação
- Mantenha objetividade na análise
- Se não houver alertas graves, retorne uma lista vazia em "alertas"
- Categorias devem ser apenas as que se aplicam ao comentário
- Temas principais devem sintetizar o conteúdo do comentário
"""

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
                "X-Title": "VIVAMENTE 360º - Análise de Sentimento"
            }

            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,  # Temperatura mais baixa para análise mais consistente
                "max_tokens": 1000,
                "response_format": {"type": "json_object"}
            }

            response = requests.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
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
        except Exception as e:
            logger.error(f"Erro inesperado na análise de sentimento: {e}")
            return None

    @classmethod
    def analisar_comentario(cls, comentario: str) -> Optional[Dict]:
        """
        Analisa o sentimento de um comentário e retorna resultados estruturados

        Args:
            comentario: Texto do comentário a ser analisado

        Returns:
            Dicionário com análise de sentimento ou None em caso de erro
        """
        if not comentario or not comentario.strip():
            logger.warning("Comentário vazio recebido para análise")
            return None

        # Limitar tamanho do comentário para evitar custos excessivos
        comentario_limpo = comentario.strip()[:2000]

        # Montar prompt
        prompt = cls.PROMPT_ANALISE_SENTIMENTO.format(comentario=comentario_limpo)

        # Chamar API
        resultado = cls._call_openrouter_api(prompt)

        if not resultado:
            logger.error("Falha ao obter resultado da análise de sentimento")
            return None

        # Validar score está no range correto
        score = resultado.get('score', 0.0)
        if score < -1.0:
            score = -1.0
        elif score > 1.0:
            score = 1.0
        resultado['score'] = round(score, 2)

        return resultado

    @classmethod
    def processar_resposta(cls, survey_response) -> bool:
        """
        Processa análise de sentimento para uma SurveyResponse e atualiza o modelo

        Args:
            survey_response: Instância de SurveyResponse

        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            # Verificar se há comentário
            if not survey_response.comentario_livre:
                logger.info(f"SurveyResponse {survey_response.id} não possui comentário livre")
                return False

            # Se já foi analisado, pular
            if survey_response.sentimento_score is not None:
                logger.info(f"SurveyResponse {survey_response.id} já possui análise de sentimento")
                return True

            # Analisar comentário
            analise = cls.analisar_comentario(survey_response.comentario_livre)

            if not analise:
                logger.error(f"Falha ao analisar comentário da SurveyResponse {survey_response.id}")
                return False

            # Atualizar modelo
            survey_response.sentimento_score = analise.get('score')
            survey_response.sentimento_categorias = {
                'sentimento_geral': analise.get('sentimento_geral'),
                'categorias': analise.get('categorias', []),
                'pontos_destaque': analise.get('pontos_destaque', []),
                'alertas': analise.get('alertas', []),
                'temas_principais': analise.get('temas_principais', [])
            }
            survey_response.save(update_fields=['sentimento_score', 'sentimento_categorias'])

            logger.info(f"Análise de sentimento processada com sucesso para SurveyResponse {survey_response.id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao processar análise de sentimento: {e}")
            return False
