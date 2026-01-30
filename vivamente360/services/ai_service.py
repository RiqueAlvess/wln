import json
import requests
from typing import Dict, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class AIService:
    """
    Serviço centralizado para integração com OpenRouter AI (GPT-4o)

    Este serviço fornece métodos genéricos para chamadas à API do OpenRouter,
    permitindo reutilização e centralização da lógica de comunicação com a IA.
    """

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base_url = settings.OPENROUTER_BASE_URL

    def completar(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        response_format: Optional[Dict] = None,
        timeout: int = 60
    ) -> Dict:
        """
        Envia prompt para GPT-4o via OpenRouter e retorna resposta estruturada

        Args:
            prompt: Texto do prompt a ser enviado
            max_tokens: Número máximo de tokens na resposta (padrão: 2000)
            temperature: Controle de criatividade 0.0-1.0 (padrão: 0.3 para respostas consistentes)
            response_format: Formato da resposta (ex: {'type': 'json_object'})
            timeout: Tempo limite da requisição em segundos (padrão: 60)

        Returns:
            Dicionário com:
                - success: bool - Se a chamada foi bem-sucedida
                - content: dict/str - Conteúdo da resposta (parseado se JSON)
                - tokens_used: dict - Informações de uso de tokens
                - error: str - Mensagem de erro (se success=False)
        """
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY não configurada")
            return {
                'success': False,
                'error': 'OPENROUTER_API_KEY não configurada'
            }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://vivamente360.com.br',
            'X-Title': 'VIVAMENTE 360º'
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature
        }

        # Adicionar formato de resposta se especificado
        if response_format:
            payload['response_format'] = response_format

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            data = response.json()
            content = data['choices'][0]['message']['content']

            # Tentar parsear JSON se response_format foi 'json_object'
            parsed_content = content
            if response_format and response_format.get('type') == 'json_object':
                try:
                    # Remove markdown code blocks se existirem
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    parsed_content = json.loads(content.strip())
                except json.JSONDecodeError as e:
                    logger.warning(f"Falha ao parsear JSON da resposta: {e}")
                    parsed_content = content

            return {
                'success': True,
                'content': parsed_content,
                'tokens_used': data.get('usage', {})
            }

        except requests.exceptions.Timeout:
            error_msg = f'Timeout ao chamar OpenRouter API após {timeout}s'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except requests.exceptions.RequestException as e:
            error_msg = f'Erro ao chamar OpenRouter API: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except (KeyError, IndexError) as e:
            error_msg = f'Formato de resposta inesperado da API: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f'Erro inesperado: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def analisar_setor(self, setor_data: Dict) -> Dict:
        """
        Gera análise completa de um setor usando IA

        Args:
            setor_data: Dicionário com dados do setor:
                - setor_nome: str
                - empresa_nome: str
                - cnae: str
                - total_respostas: int
                - periodo: str
                - scores_formatados: str
                - comentarios: str

        Returns:
            Dicionário com resultado da análise (ver método completar)
        """
        from services.ai_prompts import PROMPT_ANALISE_SETOR

        prompt = PROMPT_ANALISE_SETOR.format(**setor_data)
        return self.completar(
            prompt,
            max_tokens=3000,
            temperature=0.7,
            response_format={'type': 'json_object'}
        )

    def analisar_sentimento(self, comentario: str) -> Dict:
        """
        Analisa sentimento de um comentário

        Args:
            comentario: Texto do comentário a ser analisado

        Returns:
            Dicionário com resultado da análise de sentimento
        """
        from services.ai_prompts import PROMPT_ANALISE_SENTIMENTO

        # Limitar tamanho do comentário
        comentario_limpo = comentario.strip()[:2000]

        prompt = PROMPT_ANALISE_SENTIMENTO.format(comentario=comentario_limpo)
        return self.completar(
            prompt,
            max_tokens=1000,
            temperature=0.3,
            response_format={'type': 'json_object'}
        )

    def gerar_plano_acao(self, risco_data: Dict) -> Dict:
        """
        Sugere plano de ação baseado no risco identificado

        Args:
            risco_data: Dicionário com dados do risco:
                - dimensao: str
                - nivel_risco: str
                - score: float
                - setor_nome: str
                - evidencias: list[str]

        Returns:
            Dicionário com sugestões de plano de ação
        """
        from services.ai_prompts import PROMPT_PLANO_ACAO

        prompt = PROMPT_PLANO_ACAO.format(**risco_data)
        return self.completar(
            prompt,
            max_tokens=2000,
            temperature=0.5,
            response_format={'type': 'json_object'}
        )

    def gerar_recomendacoes(self, contexto: str, max_tokens: int = 1500) -> Dict:
        """
        Gera recomendações genéricas baseadas em um contexto fornecido

        Args:
            contexto: Texto descrevendo a situação/contexto
            max_tokens: Número máximo de tokens na resposta

        Returns:
            Dicionário com recomendações geradas
        """
        prompt = f"""
Baseado no contexto abaixo, gere recomendações práticas e viáveis:

CONTEXTO:
{contexto}

RESPONDA EM JSON:
```json
{{
  "recomendacoes": [
    {{
      "titulo": "Título da recomendação",
      "descricao": "Descrição detalhada",
      "prioridade": "Alta|Média|Baixa",
      "prazo_sugerido": "Curto|Médio|Longo prazo",
      "impacto_esperado": "Descrição do impacto"
    }}
  ]
}}
```
"""
        return self.completar(
            prompt,
            max_tokens=max_tokens,
            temperature=0.5,
            response_format={'type': 'json_object'}
        )

    @classmethod
    def criar_instancia(cls) -> 'AIService':
        """
        Factory method para criar uma instância do serviço

        Returns:
            Nova instância de AIService
        """
        return cls()
