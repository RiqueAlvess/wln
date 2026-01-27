# Comando: gerar_dados_demo

Este comando gera dados de demonstração para testes e apresentações do sistema VIVAMENTE 360º.

## O que o comando faz

- Cria ou utiliza estruturas organizacionais existentes (unidades, setores, cargos)
- Gera convites de pesquisa (SurveyInvitation) marcados como utilizados
- Cria respostas de pesquisa (SurveyResponse) com dados demográficos e respostas aleatórias
- Distribui as respostas ao longo dos últimos 30 dias para simular um período real de coleta

## Uso Básico

```bash
# Gera 100 colaboradores com respostas na primeira campanha ativa
python manage.py gerar_dados_demo

# Gera 100 colaboradores em uma campanha específica
python manage.py gerar_dados_demo --campaign-id=1

# Gera 200 colaboradores
python manage.py gerar_dados_demo --quantidade=200

# Combinar opções
python manage.py gerar_dados_demo --campaign-id=1 --quantidade=150
```

## Parâmetros

### --campaign-id (opcional)
- **Tipo**: Inteiro
- **Descrição**: ID da campanha onde os dados serão criados
- **Padrão**: Usa a primeira campanha com status "active", ou a primeira campanha disponível

### --quantidade (opcional)
- **Tipo**: Inteiro
- **Descrição**: Quantidade de colaboradores a gerar
- **Padrão**: 100

## Pré-requisitos

Antes de executar o comando, certifique-se de que:

1. Existe pelo menos uma campanha no sistema
2. Existem perguntas cadastradas e ativas (execute os seeds de perguntas primeiro)

## Dados Gerados

### Estruturas Organizacionais Criadas

**Unidades** (5 unidades):
- Matriz
- Filial São Paulo
- Filial Rio de Janeiro
- Filial Belo Horizonte
- Filial Curitiba

**Setores** (distribuídos aleatoriamente entre as unidades):
- Administrativo
- Comercial
- Financeiro
- Recursos Humanos
- TI
- Operações
- Marketing
- Atendimento
- Logística
- Qualidade

**Cargos** (12 cargos):
- Analista Jr, Pl, Sr
- Assistente
- Coordenador
- Gerente
- Diretor
- Especialista
- Supervisor
- Técnico
- Auxiliar
- Trainee

### Dados Demográficos

Os dados demográficos são gerados aleatoriamente:

- **Faixa Etária**: 18-24, 25-34, 35-49, 50-59, 60+
- **Tempo de Empresa**: 0-1, 1-3, 3-5, 5-10, 10+ anos
- **Gênero**: M, F, O, N (Prefiro não informar)

### Respostas às Perguntas

- Escala Likert de 1 a 5
- Distribuição realista: 70% das respostas entre 3-5, 30% entre 1-2
- Todas as perguntas ativas recebem resposta

### Status dos Convites

- Todos os convites são criados com status "used" (utilizados)
- Data de envio e uso distribuídas nos últimos 30 dias
- LGPD aceito automaticamente

## Exemplo de Saída

```
Usando campanha: Pesquisa de Clima 2026
  Unidade criada: Matriz
  Unidade criada: Filial São Paulo
Encontradas 45 perguntas
Gerando 100 colaboradores com respostas...
  10/100 colaboradores criados...
  20/100 colaboradores criados...
  ...
  100/100 colaboradores criados...

✓ 100 colaboradores com respostas criados com sucesso!
```

## Notas Importantes

- O comando usa transações do banco de dados, então em caso de erro, nenhum dado é criado
- Os emails gerados são fictícios (demo1@example.com, demo2@example.com, etc.)
- Os dados são distribuídos aleatoriamente entre as estruturas organizacionais
- Ideal para gerar dashboards de demonstração e testar relatórios

## Limpando Dados de Demonstração

Para remover os dados de demonstração, você pode:

```bash
# Deletar respostas de uma campanha específica
python manage.py shell
>>> from apps.responses.models import SurveyResponse
>>> SurveyResponse.objects.filter(campaign_id=1).delete()

# Deletar convites de demonstração
>>> from apps.invitations.models import SurveyInvitation
>>> SurveyInvitation.objects.filter(email_encrypted__startswith='demo').delete()
```
