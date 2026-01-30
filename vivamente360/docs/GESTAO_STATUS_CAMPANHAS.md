# Gestão de Status de Campanhas e Invalidação de Links

## Visão Geral

Esta funcionalidade implementa um sistema completo de gestão de status de campanhas com invalidação automática de links quando uma campanha é encerrada (manual ou automaticamente).

## Funcionalidades Implementadas

### 1. Gestão Manual de Status

Permite que usuários RH alterem o status de uma campanha através de uma interface amigável.

#### Status Disponíveis:
- **Rascunho**: Campanha em preparação, não aceita respostas
- **Ativa**: Campanha em andamento, aceitando respostas
- **Encerrada**: Campanha finalizada, links invalidados

#### Como Usar:
1. Acesse a página de detalhes de uma campanha
2. Clique no botão "Gerenciar Status" na seção de Ações Rápidas
3. Selecione o novo status desejado
4. Para encerrar: revise o aviso sobre invalidação de links
5. Confirme a alteração

#### URL de Acesso:
```
/surveys/<campaign_id>/manage-status/
```

### 2. Invalidação de Links ao Encerrar

Quando uma campanha é encerrada (manual ou automaticamente):

✅ Todos os convites com status `pending` são marcados como `expired`
✅ Todos os convites com status `sent` são marcados como `expired`
✅ Colaboradores não conseguem mais acessar os links
✅ Campo `updated_at` é atualizado com timestamp do encerramento

**Importante**: Convites já utilizados (`status='used'`) não são alterados.

### 3. Encerramento Automático por Data

Campanhas que ultrapassam a `data_fim` são automaticamente encerradas.

#### Configuração do Cron Job

Para executar a verificação diariamente, adicione ao crontab:

```bash
# Editar crontab
crontab -e

# Adicionar linha (executa todo dia às 00:30)
30 0 * * * cd /path/to/vivamente360 && /path/to/venv/bin/python manage.py verificar_campanhas_expiradas >> /var/log/vivamente360/campanhas_expiradas.log 2>&1
```

#### Execução Manual

```bash
# Via management command
python manage.py verificar_campanhas_expiradas

# Saída esperada:
# Iniciando verificação de campanhas expiradas...
# Concluído! 2 campanha(s) encerrada(s), 150 convite(s) invalidado(s).
#   - Campanha Q4 2025 (Empresa ABC): 75 convite(s) invalidado(s)
#   - Avaliação Anual (Empresa XYZ): 75 convite(s) invalidado(s)
```

#### Execução Programática

```python
from tasks.campaign_tasks import verificar_campanhas_expiradas

# Executar task
estatisticas = verificar_campanhas_expiradas()

# Retorna:
# {
#     'campanhas_encerradas': 2,
#     'total_convites_invalidados': 150,
#     'detalhes': [
#         {
#             'campanha_id': 123,
#             'campanha_nome': 'Campanha Q4 2025',
#             'empresa': 'Empresa ABC',
#             'data_fim': '2025-12-31',
#             'convites_invalidados': 75
#         },
#         ...
#     ]
# }
```

## API de Métodos

### Campaign.encerrar()

Encerra a campanha e invalida convites ativos.

```python
from apps.surveys.models import Campaign

campanha = Campaign.objects.get(id=123)
resultado = campanha.encerrar()

# Retorna:
# {
#     'success': True,
#     'invalidated_count': 150,
#     'message': 'Campanha encerrada com sucesso. 150 convite(s) invalidado(s).'
# }
```

### Campaign.contar_convites_ativos()

Retorna estatísticas sobre convites ativos.

```python
from apps.surveys.models import Campaign

campanha = Campaign.objects.get(id=123)
info = campanha.contar_convites_ativos()

# Retorna:
# {
#     'pendentes': 45,
#     'enviados': 120,
#     'total_ativos': 165
# }
```

## Arquivos Modificados/Criados

### Modelos
- `apps/surveys/models.py` - Métodos `encerrar()` e `contar_convites_ativos()`

### Tasks
- `tasks/campaign_tasks.py` - Task `verificar_campanhas_expiradas()`

### Management Commands
- `apps/surveys/management/commands/verificar_campanhas_expiradas.py`

### Views
- `apps/surveys/views.py` - View `CampaignManageStatusView`

### Templates
- `templates/campaigns/manage_status.html` - Interface de gestão de status
- `templates/campaigns/detail.html` - Adicionado botão "Gerenciar Status"

### URLs
- `apps/surveys/urls.py` - Rota `manage_status`

### Testes
- `tests/test_campaign_status.py` - Testes unitários completos

## Testes

Execute os testes unitários para validar a funcionalidade:

```bash
# Todos os testes
python manage.py test tests.test_campaign_status

# Teste específico
python manage.py test tests.test_campaign_status.CampaignStatusTestCase.test_encerrar_campanha_ativa
```

### Cobertura de Testes:
✅ Contagem de convites ativos
✅ Encerramento de campanha ativa
✅ Tentativa de encerrar campanha já encerrada
✅ Verificação automática de campanhas expiradas
✅ Preservação de convites já utilizados
✅ Task sem campanhas expiradas
✅ Não encerramento de campanhas draft ou closed

## Logs

A task de verificação gera logs estruturados:

```python
# INFO - Sucesso
"Campanha 123 (Avaliação Q1) encerrada automaticamente. 45 convite(s) invalidado(s)."

# WARNING - Campanha já encerrada
"Campanha 123 (Avaliação Q1) não pôde ser encerrada: Campanha já está encerrada."

# ERROR - Erro ao processar
"Erro ao encerrar campanha 123 (Avaliação Q1): [mensagem de erro]"

# INFO - Resumo final
"Task concluída: 3 campanha(s) encerrada(s), 450 convite(s) invalidado(s)."
```

## Segurança

✅ Apenas usuários com permissão RH podem alterar status
✅ Validação de status antes de aplicar mudanças
✅ Confirmação visual antes de encerrar campanha
✅ Ação de encerramento é irreversível (design intencional)
✅ Logs de auditoria via logging padrão do Django

## Melhorias Futuras (Opcional)

- [ ] Adicionar histórico de mudanças de status
- [ ] Notificar responsáveis quando campanha for encerrada automaticamente
- [ ] Dashboard com métricas de campanhas encerradas
- [ ] Opção de "reabrir" campanha (com nova data_fim)
- [ ] Exportar relatório de convites invalidados

## Suporte

Para dúvidas ou problemas:
1. Consulte os logs em `/var/log/vivamente360/`
2. Execute os testes unitários
3. Verifique permissões de usuário
4. Consulte a equipe de desenvolvimento
