"""
Prompts reutilizáveis para integração com OpenRouter AI

Este módulo centraliza todos os prompts utilizados nos diferentes
serviços de análise via IA, facilitando manutenção e consistência.
"""

# ============================================================================
# ANÁLISE DE SENTIMENTO
# ============================================================================

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

# ============================================================================
# ANÁLISE DE SETOR
# ============================================================================

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

# ============================================================================
# PLANO DE AÇÃO
# ============================================================================

PROMPT_PLANO_ACAO = """
Você é um consultor especializado em Saúde e Segurança do Trabalho.
Sugira um plano de ação detalhado baseado no risco identificado.

## DADOS DO RISCO
- Dimensão: {dimensao}
- Nível de Risco: {nivel_risco}
- Score: {score}
- Setor: {setor_nome}

## EVIDÊNCIAS
{evidencias}

## FORMATO DE RESPOSTA (OBRIGATÓRIO)
Responda EXATAMENTE neste formato JSON:
```json
{{
  "titulo": "Título do plano de ação",
  "objetivo": "Objetivo principal do plano",
  "acoes_imediatas": [
    {{
      "acao": "Descrição da ação",
      "responsavel": "Cargo/área responsável",
      "prazo": "X dias/semanas",
      "recursos_necessarios": "Lista de recursos"
    }}
  ],
  "acoes_medio_prazo": [
    {{
      "acao": "Descrição da ação",
      "responsavel": "Cargo/área responsável",
      "prazo": "X meses",
      "recursos_necessarios": "Lista de recursos"
    }}
  ],
  "acoes_preventivas": [
    {{
      "acao": "Descrição da ação preventiva",
      "frequencia": "Diária|Semanal|Mensal|Trimestral",
      "responsavel": "Cargo/área responsável"
    }}
  ],
  "indicadores_monitoramento": [
    {{
      "indicador": "Nome do indicador",
      "meta": "Meta a ser atingida",
      "frequencia_medicao": "Frequência de medição"
    }}
  ],
  "investimento_estimado": {{
    "valor_minimo": "Valor em R$",
    "valor_maximo": "Valor em R$",
    "justificativa": "Justificativa do investimento"
  }},
  "beneficios_esperados": [
    "Benefício 1",
    "Benefício 2",
    "Benefício 3"
  ],
  "riscos_nao_acao": [
    "Risco 1 de não agir",
    "Risco 2 de não agir"
  ]
}}
```

IMPORTANTE:
- Seja específico e prático nas recomendações
- Considere a viabilidade financeira e operacional
- Priorize ações de maior impacto
- Inclua indicadores mensuráveis
- Destaque os riscos de não agir
"""

# ============================================================================
# ANÁLISE DE TENDÊNCIAS
# ============================================================================

PROMPT_ANALISE_TENDENCIAS = """
Você é um analista de dados especializado em People Analytics.
Analise as tendências abaixo e forneça insights acionáveis.

## DADOS HISTÓRICOS
{dados_historicos}

## PERÍODO DE ANÁLISE
{periodo_analise}

## FORMATO DE RESPOSTA (OBRIGATÓRIO)
Responda EXATAMENTE neste formato JSON:
```json
{{
  "tendencia_geral": "Melhoria|Piora|Estável|Flutuante",
  "insights_principais": [
    {{
      "insight": "Descrição do insight",
      "evidencia": "Dados que suportam o insight",
      "importancia": "Alta|Média|Baixa"
    }}
  ],
  "padroes_identificados": [
    {{
      "padrao": "Descrição do padrão",
      "periodicidade": "Diário|Semanal|Mensal|Sazonal",
      "possivel_causa": "Hipótese sobre a causa"
    }}
  ],
  "alertas": [
    {{
      "tipo": "Tipo de alerta",
      "descricao": "Descrição do alerta",
      "urgencia": "Alta|Média|Baixa"
    }}
  ],
  "previsoes": [
    {{
      "metrica": "Nome da métrica",
      "valor_previsto": "Valor previsto",
      "horizonte": "Período da previsão",
      "confianca": "Alta|Média|Baixa"
    }}
  ],
  "recomendacoes_estrategicas": [
    "Recomendação 1",
    "Recomendação 2",
    "Recomendação 3"
  ]
}}
```

IMPORTANTE:
- Base suas análises estritamente nos dados fornecidos
- Identifique padrões sazonais e cíclicos
- Destaque mudanças significativas
- Seja conservador nas previsões
- Relacione tendências com possíveis causas
"""

# ============================================================================
# COMPARAÇÃO ENTRE SETORES
# ============================================================================

PROMPT_COMPARACAO_SETORES = """
Você é um consultor de RH especializado em análises comparativas.
Compare os setores abaixo e identifique diferenças significativas.

## DADOS DOS SETORES
{dados_setores}

## FORMATO DE RESPOSTA (OBRIGATÓRIO)
Responda EXATAMENTE neste formato JSON:
```json
{{
  "resumo_executivo": "Resumo de 2-3 parágrafos",
  "setores_destaque": {{
    "melhor_desempenho": {{
      "setor": "Nome do setor",
      "motivos": ["Motivo 1", "Motivo 2"],
      "boas_praticas": ["Prática 1", "Prática 2"]
    }},
    "maior_atencao": {{
      "setor": "Nome do setor",
      "motivos": ["Motivo 1", "Motivo 2"],
      "acoes_urgentes": ["Ação 1", "Ação 2"]
    }}
  }},
  "diferencas_significativas": [
    {{
      "dimensao": "Nome da dimensão",
      "diferencas": "Descrição das diferenças",
      "possivel_causa": "Hipótese sobre a causa"
    }}
  ],
  "oportunidades_benchmark": [
    {{
      "setor_origem": "Setor com boa prática",
      "pratica": "Descrição da prática",
      "setores_destinatarios": ["Setor 1", "Setor 2"],
      "beneficio_esperado": "Descrição do benefício"
    }}
  ],
  "recomendacoes_gerais": [
    "Recomendação 1",
    "Recomendação 2"
  ]
}}
```

IMPORTANTE:
- Identifique padrões entre setores similares
- Destaque outliers (positivos e negativos)
- Sugira transferência de boas práticas
- Seja objetivo e baseado em dados
- Considere contextos específicos de cada setor
"""

# ============================================================================
# SÍNTESE EXECUTIVA
# ============================================================================

PROMPT_SINTESE_EXECUTIVA = """
Você é um consultor executivo preparando um relatório para a alta liderança.
Sintetize os dados abaixo em um formato executivo claro e acionável.

## DADOS COMPLETOS
{dados_completos}

## FORMATO DE RESPOSTA (OBRIGATÓRIO)
Responda EXATAMENTE neste formato JSON:
```json
{{
  "mensagem_principal": "Frase resumindo a situação geral",
  "status_geral": "Positivo|Neutro|Preocupante|Crítico",
  "numeros_chave": [
    {{
      "metrica": "Nome da métrica",
      "valor": "Valor atual",
      "comparacao": "Comparação com período anterior",
      "interpretacao": "O que significa"
    }}
  ],
  "destaques_positivos": [
    "Destaque 1",
    "Destaque 2"
  ],
  "areas_preocupacao": [
    {{
      "area": "Nome da área",
      "problema": "Descrição do problema",
      "impacto": "Alto|Médio|Baixo",
      "acao_sugerida": "Primeira ação recomendada"
    }}
  ],
  "decisoes_necessarias": [
    {{
      "decisao": "O que precisa ser decidido",
      "prazo": "Urgência da decisão",
      "impacto_nao_decisao": "Consequência de não decidir"
    }}
  ],
  "proximos_passos": [
    {{
      "passo": "Descrição do passo",
      "responsavel_sugerido": "Quem deve liderar",
      "prazo_sugerido": "Quando deve ser feito"
    }}
  ]
}}
```

IMPORTANTE:
- Use linguagem executiva (clara, direta, sem jargões)
- Priorize informações acionáveis
- Quantifique sempre que possível
- Destaque o que requer decisão imediata
- Seja conciso mas completo
"""

# ============================================================================
# ANÁLISE DE COMENTÁRIOS PARA FATORES DE RISCO PSICOSSOCIAL (NR-1)
# ============================================================================

PROMPT_ANALISE_COMENTARIOS_RISCO = """
Você é um especialista em Saúde Ocupacional e Psicologia do Trabalho.
Analise os comentários de colaboradores de uma empresa para identificar
riscos psicossociais conforme a NR-1.

## COMENTÁRIOS PARA ANÁLISE
{comentarios_formatados}

## CONTEXTO
- Empresa: {empresa_nome}
- CNAE: {cnae} ({cnae_descricao})
- Setor: {setor_nome}
- Total de comentários: {total_comentarios}
- Score médio HSE-IT do setor: {score_medio}

## FATORES DE RISCO NR-1 (REFERÊNCIA)
### Organização do Trabalho
- ORG_001: Sobrecarga de Trabalho
- ORG_002: Ritmo de Trabalho Intenso
- ORG_003: Prazos Excessivamente Curtos
- ORG_004: Jornadas Longas ou Imprevisíveis
- ORG_005: Falta de Clareza de Papéis

### Conteúdo do Trabalho
- CON_001: Tarefas Monótonas ou Repetitivas
- CON_002: Fragmentação Excessiva
- CON_003: Subutilização de Habilidades
- CON_004: Alta Demanda Emocional

### Relações Interpessoais
- REL_001: Assédio Moral
- REL_002: Assédio Sexual
- REL_003: Falta de Apoio
- REL_004: Isolamento Social
- REL_005: Gestão Autoritária

### Fatores Individuais/Contextuais
- IND_001: Insegurança no Emprego
- IND_002: Desequilíbrio Vida-Trabalho
- IND_003: Exposição a Violência
- IND_004: Traumas Ocupacionais

## RESPONDA EM JSON ESTRUTURADO

```json
{{
  "resumo_geral": {{
    "sentimento_predominante": "Positivo|Neutro|Negativo|Misto",
    "score_sentimento": 0.0,
    "nivel_preocupacao": "Baixo|Médio|Alto|Crítico"
  }},

  "fatores_identificados": [
    {{
      "codigo_fator": "ORG_001",
      "nome_fator": "Sobrecarga de Trabalho",
      "frequencia_mencoes": 5,
      "evidencias": [
        "Trecho relevante do comentário 1",
        "Trecho relevante do comentário 2"
      ],
      "ajuste_probabilidade": 1,
      "justificativa_ajuste": "Múltiplas menções explícitas a excesso de trabalho"
    }}
  ],

  "alertas_criticos": [
    {{
      "tipo": "Assédio Moral|Assédio Sexual|Burnout|Ideação Suicida|Violência|Discriminação",
      "gravidade": "Alta|Crítica",
      "evidencia": "Trecho exato do comentário",
      "recomendacao_imediata": "Ação específica recomendada",
      "encaminhamento": "RH|Jurídico|SESMT|Psicólogo|Ouvidoria"
    }}
  ],

  "temas_recorrentes": [
    {{
      "tema": "Nome do tema",
      "frequencia": 10,
      "sentimento": "Positivo|Negativo|Neutro",
      "palavras_chave": ["palavra1", "palavra2"]
    }}
  ],

  "pontos_positivos": [
    {{
      "aspecto": "O que está funcionando bem",
      "frequencia": 3,
      "impacto": "Alto|Médio|Baixo"
    }}
  ],

  "recomendacoes_gerais": [
    {{
      "prioridade": 1,
      "acao": "Descrição da ação recomendada",
      "fator_relacionado": "ORG_001",
      "prazo_sugerido": "Imediato|30 dias|90 dias|180 dias"
    }}
  ]
}}
```

## REGRAS IMPORTANTES
1. Mantenha TOTAL ANONIMATO - nunca identifique pessoas
2. Seja objetivo e baseado apenas nos textos fornecidos
3. Se identificar risco de SUICÍDIO ou VIOLÊNCIA, marque como alerta CRÍTICO
4. O ajuste_probabilidade só pode ser -1, 0 ou +1:
   - +1: Comentários evidenciam que o risco é MAIOR que o score sugere
   - 0: Comentários são consistentes com o score
   - -1: Comentários sugerem que o risco é MENOR que o score
5. Correlacione com os códigos de fatores NR-1 quando possível
6. Destaque tanto problemas quanto pontos positivos
7. score_sentimento: -1.0 (muito negativo) a 1.0 (muito positivo)
"""
