# Campo de Feedback + Análise de Sentimento com IA

## 📋 Visão Geral

Esta feature adiciona um campo de feedback livre ao final do questionário, permitindo que colaboradores expressem seus sentimentos e opiniões com suas próprias palavras. A IA analisa automaticamente esses comentários e correlaciona com dados quantitativos para gerar insights mais profundos.

## 🎯 Objetivos

- Capturar feedback qualitativo dos colaboradores
- Identificar automaticamente sentimentos e emoções
- Detectar alertas críticos (assédio, burnout, discriminação)
- Complementar análises quantitativas com percepções humanas
- Manter total anonimato e privacidade

## 🏗️ Arquitetura

### 1. Modelo de Dados

**Arquivo**: `vivamente360/apps/responses/models.py`

```python
class SurveyResponse(TimeStampedModel):
    # ... campos existentes ...

    # Campo de feedback livre
    comentario_livre = models.TextField(
        blank=True,
        help_text="Comentário opcional do colaborador"
    )

    # Análise de sentimento (preenchido pela IA)
    sentimento_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="-1.0 (muito negativo) a 1.0 (muito positivo)"
    )

    sentimento_categorias = models.JSONField(
        null=True,
        blank=True,
        help_text="Categorias e análise identificada pela IA"
    )
```

### 2. Serviço de Análise de Sentimento

**Arquivo**: `vivamente360/services/sentiment_service.py`

O `SentimentService` utiliza a API do OpenRouter (GPT-4o) para:

- Analisar o sentimento geral do comentário (score de -1.0 a 1.0)
- Categorizar em temas (Sobrecarga, Reconhecimento, Liderança, etc.)
- Identificar pontos de destaque (Preocupações, Elogios, Sugestões)
- Detectar alertas críticos (Assédio, Burnout, Discriminação, etc.)
- Extrair temas principais

**Métodos principais**:
- `analisar_comentario(comentario: str)` - Analisa um comentário individual
- `processar_resposta(survey_response)` - Processa e atualiza uma SurveyResponse

### 3. Interface do Usuário

**Arquivo**: `vivamente360/templates/survey/step_feedback.html`

Nova tela adicionada ao fluxo do questionário:

- **Posição**: Após todas as perguntas quantitativas
- **Características**:
  - Campo de texto livre com limite de 500 caracteres
  - Contador de caracteres em tempo real
  - Botões: "Pular" (opcional) e "Enviar e Finalizar"
  - Avisos de privacidade e anonimato
  - Design consistente com o restante do questionário

### 4. Fluxo do Questionário Atualizado

1. **LGPD** → Aceite de termos
2. **Demografia** → Dados demográficos anônimos
3. **Perguntas** → Questões do HSE-IT (escala 0-4)
4. **Feedback** ⭐ **NOVO** → Campo de texto livre
5. **Sucesso** → Confirmação de envio

## 🔄 Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Colaborador preenche o questionário                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Última pergunta → Redireciona para step_feedback         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Colaborador escreve comentário livre (ou pula)           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. SurveyResponse criada com comentario_livre               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. SentimentService.processar_resposta() chamado            │
│    - Envia comentário para GPT-4o via OpenRouter            │
│    - Recebe análise estruturada em JSON                     │
│    - Atualiza sentimento_score e sentimento_categorias      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Notificações enviadas (incluindo alertas de sentimento)  │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Estrutura da Análise de Sentimento

### Score de Sentimento
- **-1.0**: Muito negativo
- **-0.5**: Negativo
- **0.0**: Neutro
- **+0.5**: Positivo
- **+1.0**: Muito positivo

### Categorias Identificadas
- Sobrecarga de trabalho
- Reconhecimento profissional
- Liderança e gestão
- Relacionamento com colegas
- Ambiente físico de trabalho
- Desenvolvimento de carreira
- Saúde e bem-estar

### Tipos de Pontos Destacados
- **Preocupação**: Questões que precisam atenção
- **Elogio**: Aspectos positivos mencionados
- **Sugestão**: Ideias de melhoria
- **Desabafo**: Expressão de sentimentos

### Alertas Críticos
- **Assédio**: Moral ou sexual
- **Burnout**: Esgotamento profissional
- **Conflito Grave**: Conflitos interpessoais sérios
- **Saúde Mental**: Questões psicológicas
- **Discriminação**: Qualquer forma de preconceito

## 🔐 Privacidade e Segurança

### Garantias de Anonimato

1. **Não identificação**: Campo é opcional e anônimo
2. **Avisos claros**: Usuário é alertado para não incluir informações pessoais
3. **Processamento agregado**: Comentários são analisados sem vínculo direto com identidade
4. **Conformidade LGPD**: Aceite prévio do usuário é obrigatório

### Proteção de Dados

- Comentários armazenados com criptografia no banco de dados
- Acesso restrito apenas a administradores autorizados
- Logs de acesso auditados
- API de IA (OpenRouter) não armazena dados enviados

## 🚀 Como Usar

### Para Colaboradores

1. Complete todas as perguntas do questionário
2. Na tela final de feedback:
   - Escreva livremente sobre sua experiência (até 500 caracteres)
   - Ou clique em "Pular" se preferir não comentar
3. Clique em "Enviar e Finalizar"

### Para Administradores

#### Visualizar Análises de Sentimento

```python
from apps.responses.models import SurveyResponse

# Buscar respostas com feedback
respostas_com_feedback = SurveyResponse.objects.filter(
    comentario_livre__isnull=False
).exclude(comentario_livre='')

# Ver análise de sentimento
for resposta in respostas_com_feedback:
    print(f"Score: {resposta.sentimento_score}")
    print(f"Categorias: {resposta.sentimento_categorias}")
```

#### Análise Manual de Comentário

```python
from services.sentiment_service import SentimentService

comentario = "Estou muito feliz trabalhando aqui, mas sinto falta de reconhecimento"
analise = SentimentService.analisar_comentario(comentario)
print(analise)
```

## 📈 Integração com Análise de Setor

O `SectorAnalysisService` foi atualizado para incluir comentários livres na análise por setor:

```python
# Comentários agora são incluídos no prompt da IA
## COMENTÁRIOS DOS COLABORADORES (Anônimos)
- Comentário 1...
- Comentário 2...
```

Isso permite que a IA correlacione feedback qualitativo com scores quantitativos para gerar insights mais completos.

## 🛠️ Configuração

### Variáveis de Ambiente Necessárias

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4o
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### Migrations

```bash
python manage.py migrate responses
```

## 📝 Exemplo de Resposta da IA

```json
{
  "score": 0.35,
  "sentimento_geral": "Misto",
  "categorias": ["Reconhecimento", "Liderança", "Sobrecarga"],
  "pontos_destaque": [
    {
      "tipo": "Preocupação",
      "texto_relevante": "me sinto sobrecarregado com a quantidade de trabalho",
      "gravidade": "Média"
    },
    {
      "tipo": "Elogio",
      "texto_relevante": "a equipe é muito unida e colaborativa",
      "gravidade": "N/A"
    }
  ],
  "alertas": [],
  "temas_principais": ["Carga de trabalho", "Ambiente colaborativo"]
}
```

## 🎨 Benefícios

### Para a Empresa
- **Insights qualitativos** complementam dados quantitativos
- **Detecção precoce** de problemas graves
- **Ações direcionadas** baseadas em feedback real
- **Melhoria contínua** do clima organizacional

### Para o Colaborador
- **Voz ativa** na organização
- **Anonimato garantido** para feedback honesto
- **Sensação de escuta** e valorização
- **Canal seguro** para expressar preocupações

## 🔍 Casos de Uso

### 1. Identificação de Assédio
Se um comentário menciona assédio, a IA:
- Classifica como alerta crítico
- Sugere ação imediata
- Marca para revisão prioritária

### 2. Burnout em Setor Específico
Múltiplos comentários negativos em um setor:
- Correlação com scores baixos de Saúde
- Análise de setor destaca problema
- Recomendações de intervenção geradas

### 3. Sugestões de Melhoria
Comentários construtivos:
- Identificados como "Sugestão"
- Categorizados por tema
- Compilados para gestão estratégica

## 📚 Referências

- [Modelo HSE-IT de Riscos Psicossociais](https://www.hse.gov.uk/)
- [LGPD - Lei Geral de Proteção de Dados](https://www.gov.br/lgpd/)
- [OpenRouter API Documentation](https://openrouter.ai/docs)

---

**Desenvolvido com ❤️ para VIVAMENTE 360º**
