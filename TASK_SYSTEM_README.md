# Sistema de Processamento de Tarefas e Notificações

## Visão Geral

Este documento descreve o sistema de processamento assíncrono de tarefas e notificações implementado no Vivamente 360.

## Arquitetura

O sistema é composto por:

1. **TaskQueue**: Modelo que armazena tarefas assíncronas
2. **UserNotification**: Modelo de notificações para usuários
3. **TaskProcessor**: Processador de tarefas
4. **TaskFileStorage**: Gerenciamento de arquivos gerados
5. **APIs REST**: Endpoints para consulta de tasks e notificações
6. **Interface Web**: Tela de acompanhamento de processamento

## Modelos

### TaskQueue

Armazena informações sobre tarefas assíncronas:

- `task_type`: Tipo da tarefa (export_plano_acao, send_email, etc)
- `status`: Status (pending, processing, completed, failed)
- `progress`: Progresso 0-100
- `progress_message`: Mensagem de progresso
- `file_path`, `file_name`, `file_size`: Informações do arquivo gerado
- `user`, `empresa`: Associação com usuário e empresa
- `payload`: Dados da tarefa (JSON)
- `error_message`: Mensagem de erro se falhar

### UserNotification

Notificações para usuários:

- `notification_type`: Tipo (task_completed, task_failed, file_ready, info, warning, error)
- `title`: Título da notificação
- `message`: Mensagem
- `task`: Tarefa relacionada (opcional)
- `link_url`, `link_text`: Link para ação
- `is_read`: Se foi lida
- `read_at`: Data de leitura

## Tipos de Tasks Suportadas

### Exports (Geram Arquivos)

- `export_plano_acao`: Exportação de planos de ação (DOCX)
- `export_plano_acao_rich`: Exportação detalhada de plano de ação (DOCX)
- `export_checklist_nr1`: Exportação de checklist NR-1 (PDF)
- `export_campaign_comparison`: Comparação de campanhas (DOCX)
- `export_risk_matrix_excel`: Matriz de risco (XLSX)
- `export_pgr_document`: Documento PGR (TXT)

### Outras Tasks

- `send_email`: Envio de e-mails
- `generate_sector_analysis`: Análise de setor por IA
- `import_csv`: Importação de dados CSV

## APIs Disponíveis

### Tasks API

**Base URL**: `/api/tasks/`

#### Listar Tasks
```
GET /api/tasks/
GET /api/tasks/?status=completed
GET /api/tasks/?is_file_task=true
```

#### Resumo
```
GET /api/tasks/summary/
```

Retorna:
```json
{
  "total": 10,
  "pending": 2,
  "processing": 1,
  "completed": 6,
  "failed": 1,
  "files_available": 4
}
```

#### Download de Arquivo
```
GET /api/tasks/{id}/download/
```

#### Deletar Arquivo
```
DELETE /api/tasks/{id}/delete_file/
```

### Notificações API

**Base URL**: `/api/notifications/`

#### Listar Notificações
```
GET /api/notifications/
GET /api/notifications/unread/
```

#### Contador de Não Lidas
```
GET /api/notifications/unread_count/
```

#### Marcar como Lida
```
POST /api/notifications/{id}/mark_read/
POST /api/notifications/mark_all_read/
POST /api/notifications/mark_multiple_read/
```

Payload:
```json
{
  "notification_ids": [1, 2, 3]
}
```

## Interface Web

### Tela de Processamento

**URL**: `/tasks/processing/`

Funcionalidades:

- ✅ Visualização em tempo real de tasks (auto-refresh a cada 5s)
- ✅ Resumo de tasks por status
- ✅ Filtros por status
- ✅ Download de arquivos prontos
- ✅ Indicador de progresso para tasks em andamento
- ✅ Visualização de erros

### Abas

1. **Tarefas**: Lista todas as tasks com filtros
2. **Arquivos Prontos**: Grid de arquivos disponíveis para download

## Como Usar

### 1. Criar uma Task

```python
from apps.core.models import TaskQueue

# Criar task de export
task = TaskQueue.objects.create(
    task_type='export_plano_acao',
    user=request.user,
    empresa=request.user.empresa,
    payload={
        'campaign_id': campaign.id,
        'plano_ids': [1, 2, 3]
    }
)
```

### 2. Processar Tasks (Worker)

#### Modo Single Run
```bash
python manage.py process_task_queue
```

#### Modo Worker (Contínuo)
```bash
python manage.py process_task_queue --worker --interval 10
```

#### Com Retry de Falhadas
```bash
python manage.py process_task_queue --worker --retry-failed
```

### 3. Consultar Status

```python
from apps.core.models import TaskQueue

# Buscar task
task = TaskQueue.objects.get(id=task_id)

# Verificar status
if task.status == 'completed' and task.can_download:
    # Arquivo disponível
    file_url = f'/api/tasks/{task.id}/download/'
```

### 4. Notificações

Notificações são criadas automaticamente quando:

- ✅ Task é completada com sucesso
- ✅ Task falha
- ✅ Arquivo fica pronto para download

Consultar notificações:

```python
from apps.core.models import UserNotification

# Não lidas
unread = UserNotification.objects.filter(
    user=request.user,
    is_read=False
)

# Marcar como lida
notification.mark_as_read()
```

## Gerenciamento de Arquivos

### Limpeza Automática

Remove arquivos mais antigos que X dias:

```bash
# Remover arquivos com mais de 30 dias
python manage.py cleanup_old_task_files --days 30

# Modo simulação (dry-run)
python manage.py cleanup_old_task_files --days 30 --dry-run
```

### Estrutura de Diretórios

```
media/
  task_files/
    2026/
      02/
        plano_acao/
          123_abc123de.docx
        checklist/
          124_xyz789ab.pdf
```

## Segurança

- ✅ Autenticação obrigatória para todas as APIs
- ✅ Usuários só veem suas próprias tasks
- ✅ Filtro por empresa quando aplicável
- ✅ Validação de permissões no download

## Monitoramento

### Django Admin

Acesse `/admin/core/taskqueue/` e `/admin/core/usernotification/` para:

- Visualizar todas as tasks
- Ver estatísticas
- Marcar notificações como lidas
- Debugar erros

### Logs

```python
import logging
logger = logging.getLogger(__name__)

# Logs automáticos em:
# - services/task_processors.py
# - services/task_file_storage.py
# - apps/core/api_views.py
```

## Boas Práticas

### 1. Criar Tasks de Forma Segura

```python
try:
    task = TaskQueue.objects.create(
        task_type='export_plano_acao',
        user=request.user,
        empresa=request.user.empresa,
        payload={
            'campaign_id': campaign.id,
            'plano_ids': list(planos.values_list('id', flat=True))
        }
    )
    messages.success(
        request,
        'Exportação iniciada! Acompanhe o progresso em Processamento.'
    )
except Exception as e:
    messages.error(request, f'Erro ao criar tarefa: {str(e)}')
```

### 2. Adicionar Modal de Confirmação

```html
<!-- Modal confirmando que task foi criada -->
<div class="modal fade" id="taskCreatedModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5>Tarefa Iniciada</h5>
            </div>
            <div class="modal-body">
                <p>Sua solicitação está sendo processada.</p>
                <p>Você pode acompanhar o progresso na tela de Processamento.</p>
            </div>
            <div class="modal-footer">
                <a href="{% url 'core:task_processing' %}" class="btn btn-primary">
                    Ver Processamento
                </a>
                <button class="btn btn-secondary" data-bs-dismiss="modal">
                    Continuar Aqui
                </button>
            </div>
        </div>
    </div>
</div>
```

### 3. Integrar no Navbar (Futuro)

```html
<!-- Ícone de notificações -->
<li class="nav-item dropdown">
    <a class="nav-link" href="#" id="notificationsDropdown"
       data-bs-toggle="dropdown">
        <i class="bi bi-bell"></i>
        <span class="badge bg-danger" id="notification-count">0</span>
    </a>
    <div class="dropdown-menu dropdown-menu-end" id="notifications-list">
        <!-- Notificações carregadas via AJAX -->
    </div>
</li>

<!-- Link para tela de processamento -->
<li class="nav-item">
    <a class="nav-link" href="{% url 'core:task_processing' %}">
        <i class="bi bi-list-task"></i> Processamento
    </a>
</li>
```

## Troubleshooting

### Task Não Processa

1. Verificar se worker está rodando:
   ```bash
   python manage.py process_task_queue --worker
   ```

2. Verificar logs de erro:
   ```python
   task = TaskQueue.objects.get(id=task_id)
   print(task.error_message)
   ```

### Arquivo Não Disponível

1. Verificar se task está completada:
   ```python
   task.status == 'completed'
   ```

2. Verificar se arquivo existe:
   ```python
   task.can_download  # True se arquivo disponível
   ```

### Notificações Não Aparecem

1. Verificar se task tem usuário associado:
   ```python
   task.user  # Deve estar preenchido
   ```

2. Consultar notificações diretamente:
   ```python
   UserNotification.objects.filter(user=user)
   ```

## Próximos Passos

- [ ] Adicionar ícone de notificações no navbar
- [ ] Implementar WebSocket para notificações em tempo real
- [ ] Adicionar suporte a S3 para armazenamento de arquivos
- [ ] Criar dashboard de estatísticas de tasks
- [ ] Adicionar compressão de arquivos grandes
- [ ] Implementar sistema de prioridades para tasks

## Correções Realizadas

### ✅ Bug: Erro no Export PGR
- **Problema**: `'_io.BytesIO' object has no attribute 'save'`
- **Arquivo**: `vivamente360/apps/analytics/views.py:701`
- **Solução**: Alterado de `doc.save(response)` para `response.write(doc_bio.getvalue())`

### ✅ Bug: Erro no Export Checklist NR1
- **Problema**: `'Empresa' object has no attribute 'nome_fantasia'`
- **Arquivo**: `vivamente360/services/export_service.py:289`
- **Solução**: Alterado `campaign.empresa.nome_fantasia` para `campaign.empresa.nome`
- **Arquivos corrigidos**:
  - `vivamente360/services/export_service.py`
  - `vivamente360/apps/actions/serializers.py`

## Conclusão

O sistema de processamento de tarefas e notificações está totalmente funcional e pronto para uso. Ele resolve o problema de usuários ficarem presos em telas durante processamentos longos, fornecendo:

1. ✅ Processamento assíncrono de tarefas
2. ✅ Armazenamento persistente de arquivos gerados
3. ✅ Sistema de notificações
4. ✅ Interface de acompanhamento em tempo real
5. ✅ APIs completas para integração
6. ✅ Gerenciamento administrativo

Implemente os modals de confirmação conforme necessário e adicione links para a tela de processamento onde apropriado.
