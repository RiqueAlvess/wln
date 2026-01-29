# Classificação de Riscos Psicossociais - Padrão NR-1

## Visão Geral

Este documento descreve a padronização da nomenclatura de riscos conforme a **NR-1 (Norma Regulamentadora nº 1)** implementada no sistema Vivamente360.

## Estrutura da Classificação

O sistema utiliza uma matriz de risco baseada em **Probabilidade × Severidade** para calcular o nível de risco (1-16), que é então classificado em 4 categorias:

### 🔴 CRÍTICO (Nível 13-16)
- **Nomenclatura NR-1**: Risco Intolerável
- **Cor**: Vermelho (#dc3545)
- **Ação Requerida**: Intervenção IMEDIATA obrigatória
- **Prazo Máximo**: 30 dias
- **Badge CSS**: `bg-danger`

### 🟠 IMPORTANTE (Nível 9-12)
- **Nomenclatura NR-1**: Risco Substancial
- **Cor**: Laranja (#fd7e14)
- **Ação Requerida**: Ação prioritária necessária
- **Prazo Máximo**: 60 dias
- **Badge CSS**: `bg-warning text-dark`

### 🟡 MODERADO (Nível 5-8)
- **Nomenclatura NR-1**: Risco Tolerável com Controle
- **Cor**: Amarelo (#ffc107)
- **Ação Requerida**: Monitoramento e ações preventivas
- **Prazo Máximo**: 90 dias
- **Badge CSS**: `bg-warning`

### 🟢 ACEITÁVEL (Nível 1-4)
- **Nomenclatura NR-1**: Risco Trivial
- **Cor**: Verde (#28a745)
- **Ação Requerida**: Manter controles existentes
- **Prazo Máximo**: Revisão anual
- **Badge CSS**: `bg-success`

## Implementação no Código

### 1. Definição da Estrutura

O dicionário `CLASSIFICACAO_RISCOS` está definido em `services/risk_service.py`:

```python
from services.risk_service import CLASSIFICACAO_RISCOS

# Exemplo de uso:
classificacao = CLASSIFICACAO_RISCOS['critico']
print(classificacao['nome_nr1'])  # "Risco Intolerável"
print(classificacao['prazo_max'])  # "30 dias"
```

### 2. Métodos Auxiliares

#### `RiskService.get_classificacao_por_nivel(nivel_risco: int) -> str`
Retorna a chave da classificação baseada no nível de risco (1-16).

```python
chave = RiskService.get_classificacao_por_nivel(14)  # retorna 'critico'
```

#### `RiskService.get_info_classificacao(nivel_risco: int) -> dict`
Retorna o dicionário completo com todas as informações da classificação.

```python
info = RiskService.get_info_classificacao(14)
# Retorna todo o dicionário de 'critico'
```

### 3. Cálculo do Nível de Risco

O cálculo é feito em `services/score_service.py`:

```python
# 1. Calcula score por dimensão (0-4)
score = ScoreService.calcular_score_dimensao(respostas, dimensao)

# 2. Classifica baseado no score e tipo de dimensão
risco = ScoreService.classificar_risco(score, dimensao)  # retorna probabilidade

# 3. Calcula nível de risco (probabilidade × severidade)
nivel = ScoreService.calcular_nivel_risco(probabilidade, severidade)
```

### 4. Exibição no Dashboard

A legenda de classificação está visível no dashboard (`templates/dashboard/index.html`) logo após as métricas principais, exibindo:
- Ícone emoji colorido
- Nome da classificação
- Nomenclatura NR-1
- Ação requerida
- Prazo máximo

## Fluxo de Dados

```
Respostas do Questionário (35 perguntas)
    ↓
Score por Dimensão (7 dimensões HSE-IT)
    ↓
Classificação de Risco por Dimensão (probabilidade 1-4)
    ↓
Nível de Risco = Probabilidade × Severidade (1-16)
    ↓
Classificação Final (Crítico, Importante, Moderado, Aceitável)
    ↓
Exibição no Dashboard com cores e nomenclatura NR-1
```

## Dimensões HSE-IT

O sistema avalia 7 dimensões de riscos psicossociais:

1. **Demandas** (negativa) - Carga de trabalho
2. **Controle** (positiva) - Autonomia no trabalho
3. **Apoio da Chefia** (positiva) - Suporte gerencial
4. **Apoio dos Colegas** (positiva) - Suporte social
5. **Relacionamentos** (negativa) - Conflitos interpessoais
6. **Cargo/Função** (positiva) - Clareza de papel
7. **Comunicação e Mudanças** (positiva) - Transparência organizacional

## Referências

- **NR-1**: Norma Regulamentadora nº 1 - Disposições Gerais e Gerenciamento de Riscos Ocupacionais
- **HSE-IT**: Health and Safety Executive - Indicator Tool (adaptado para o contexto brasileiro)

## Localização dos Arquivos

- **Constante Principal**: `/services/risk_service.py` (linhas 6-48)
- **Métodos de Cálculo**: `/services/score_service.py` (linhas 51-70)
- **Template Dashboard**: `/templates/dashboard/index.html` (linhas 205-258)
- **View Context**: `/apps/analytics/views.py` (linha 108)

## Histórico de Alterações

- **2026-01-29**: Implementação inicial da nomenclatura NR-1 padronizada
  - Criado dicionário `CLASSIFICACAO_RISCOS`
  - Adicionados métodos auxiliares no RiskService
  - Inserida legenda visual no dashboard
  - Documentação completa criada
