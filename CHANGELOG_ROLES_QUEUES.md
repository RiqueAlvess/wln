# Changelog - Sistema de Roles e Filas de Tarefas

## Data: 2026-02-01

## Resumo das Mudanças

Este documento descreve as principais mudanças implementadas no sistema Vivamente 360º relacionadas a:
1. **Remoção da role ADM** (substituída por superuser)
2. **Sistema de filas de tarefas em banco de dados** para exportação/importação
3. **Restrições de visualização** para usuários com role Liderança

---

## 1. Remoção da Role ADM

### Motivação
A role `admin` era redundante, pois o estado de Root (superuser) já é vinculado ao criar a conta. Isso causava confusão e duplicação de lógica de permissões.

### Mudanças Implementadas

#### 1.1. Modelo UserProfile
**Arquivo:** `vivamente360/apps/accounts/models.py`

**Antes:**
```python
ROLE_CHOICES = [
    ('admin', 'Administrador'),
    ('rh', 'RH'),
    ('lideranca', 'Liderança'),
]
```

**Depois:**
```python
ROLE_CHOICES = [
    ('rh', 'RH'),
    ('lideranca', 'Liderança'),
]
```

#### 1.2. Mixins de Permissão
**Arquivo:** `vivamente360/apps/core/mixins.py`

**Mudanças:**
- Removido `AdminRequiredMixin` (não é mais necessário)
- `RHRequiredMixin` agora aceita apenas `['rh']` + superusers
- `DashboardAccessMixin` aceita `['rh', 'lideranca']` + superusers
- Adicionado verificação `if request.user.is_superuser` em todos os mixins
- Substituído `profile.role == 'admin'` por `is_superuser` em todos os métodos

**Novos métodos adicionados ao `DashboardAccessMixin`:**
- `get_unidades_permitidas()` - Retorna unidades que o usuário pode visualizar
- `get_setores_permitidos()` - Retorna setores que o usuário pode visualizar
- `filter_unidades_by_permission(queryset)` - Filtra queryset de unidades
- `filter_setores_by_permission(queryset)` - Filtra queryset de setores

#### 1.3. Migração de Dados
**Arquivo:** `vivamente360/apps/accounts/migrations/0002_remove_admin_role.py`

**O que faz:**
1. Identifica todos os UserProfile com `role='admin'`
2. Para cada um:
   - Define `user.is_superuser = True`
   - Define `user.is_staff = True`
   - Deleta o perfil (não é mais necessário para superusers)
3. Atualiza o campo `role` do modelo para remover a opção 'admin'

### Como Aplicar
```bash
python manage.py migrate accounts
```

---

## 2. Sistema de Filas de Tarefas em Banco de Dados

### Motivação
Operações de exportação e importação de arquivos podem ser pesadas e colapsar a aplicação quando executadas sincronamente. Implementamos um sistema de filas usando o modelo `TaskQueue` do PostgreSQL.

### Arquitetura

O sistema utiliza:
- **Modelo `TaskQueue`** (já existente em `apps/core/models.py`) para armazenar tarefas
- **TaskProcessor** para processar diferentes tipos de tarefas
- **Worker** que pode rodar como comando Django ou via cron/supervisor

### Mudanças Implementadas

#### 2.1. Processadores de Tarefas
**Arquivo:** `vivamente360/services/task_processors.py` (NOVO)

**Classes implementadas:**
- `TaskProcessor` - Processa tarefas baseado no `task_type`
- `TaskQueueWorker` - Worker que processa tarefas pendentes da fila

**Tipos de tarefas suportadas:**
- `import_csv` - Importação de CSV
- `export_plano_acao` - Exportação de plano de ação (Word)
- `export_plano_acao_rich` - Exportação de plano de ação rico (Word)
- `export_checklist_nr1` - Exportação de checklist NR-1 (PDF)
- `export_campaign_comparison` - Comparação de campanhas (Word)
- `export_risk_matrix_excel` - Matriz de risco (Excel)

**Características:**
- Máximo de 3 tentativas por tarefa (configurável via `max_attempts`)
- Estados: `pending`, `processing`, `completed`, `failed`
- Registro de erros e timestamps

#### 2.2. Comando de Management
**Arquivo:** `vivamente360/apps/core/management/commands/process_task_queue.py` (NOVO)

**Uso:**
```bash
# Processar uma vez
python manage.py process_task_queue

# Executar como worker contínuo
python manage.py process_task_queue --worker

# Worker com intervalo customizado (30 segundos)
python manage.py process_task_queue --worker --interval 30

# Processar mais tarefas por batch
python manage.py process_task_queue --worker --batch-size 20

# Tentar reprocessar tarefas falhadas
python manage.py process_task_queue --retry-failed
```

#### 2.3. Atualização das Views
**Arquivo:** `vivamente360/apps/invitations/views.py`

**ImportCSVView - Antes:**
```python
def post(self, request, campaign_id):
    # ... validação ...
    result = ImportService.process_import(campaign.empresa, campaign, rows, crypto_service)
    messages.success(request, f'{result["created"]} convites importados')
```

**ImportCSVView - Depois:**
```python
def post(self, request, campaign_id):
    # ... validação ...

    # Enfileirar tarefa no banco de dados
    task = TaskQueue.objects.create(
        task_type='import_csv',
        payload={
            'campaign_id': campaign_id,
            'empresa_id': campaign.empresa.id,
            'rows': rows,
            'user_id': request.user.id
        }
    )

    messages.success(request,
        f'Importação de {len(rows)} registros enfileirada. '
        f'Você será notificado quando concluir.'
    )
```

### Como Usar

#### Opção 1: Worker Contínuo (Recomendado para Produção)

Use um supervisor como **systemd** ou **supervisor**:

**Arquivo: `/etc/systemd/system/vivamente-queue-worker.service`**
```ini
[Unit]
Description=Vivamente 360 Task Queue Worker
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/vivamente360
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python manage.py process_task_queue --worker --interval 10
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable vivamente-queue-worker
sudo systemctl start vivamente-queue-worker
sudo systemctl status vivamente-queue-worker
```

#### Opção 2: Cron Job

**Adicionar ao crontab:**
```bash
# Processar fila a cada minuto
* * * * * cd /path/to/vivamente360 && /path/to/venv/bin/python manage.py process_task_queue

# Retry de tarefas falhadas a cada 5 minutos
*/5 * * * * cd /path/to/vivamente360 && /path/to/venv/bin/python manage.py process_task_queue --retry-failed
```

#### Opção 3: Desenvolvimento

```bash
# Terminal dedicado ao worker
python manage.py process_task_queue --worker
```

### Monitoramento de Tarefas

**Via Django Admin:**
```python
# O modelo TaskQueue já está registrado no admin
# Acesse /admin/core/taskqueue/
```

**Via Shell:**
```python
from apps.core.models import TaskQueue

# Ver tarefas pendentes
TaskQueue.objects.filter(status='pending').count()

# Ver tarefas falhadas
TaskQueue.objects.filter(status='failed')

# Ver últimas tarefas concluídas
TaskQueue.objects.filter(status='completed').order_by('-completed_at')[:10]
```

---

## 3. Restrições de Visualização para Liderança

### Motivação
Usuários com role `lideranca` devem conseguir visualizar apenas dados das Unidades e Setores aos quais estão vinculados.

### Implementação

#### 3.1. Filtros Automáticos no DashboardAccessMixin
O mixin `DashboardAccessMixin` agora fornece métodos auxiliares para filtrar dados baseado na role do usuário:

**Métodos disponíveis:**
```python
# Em qualquer view que herda de DashboardAccessMixin:

# Obter unidades permitidas
unidades = self.get_unidades_permitidas()

# Obter setores permitidos
setores = self.get_setores_permitidos()

# Filtrar um queryset de unidades
unidades_filtradas = self.filter_unidades_by_permission(Unidade.objects.all())

# Filtrar um queryset de setores
setores_filtrados = self.filter_setores_by_permission(Setor.objects.all())

# Filtrar qualquer queryset com relacionamento de unidade/setor
responses = self.get_queryset_filtered(SurveyResponse.objects.all())
```

#### 3.2. Comportamento por Role

**Superuser (`is_superuser=True`):**
- Acesso completo a todos os dados
- Sem restrições

**RH (`role='rh'`):**
- Visualiza todas as unidades e setores das empresas vinculadas
- Campo: `UserProfile.empresas` (ManyToMany)

**Liderança (`role='lideranca'`):**
- Visualiza apenas unidades em `UserProfile.unidades_permitidas`
- Visualiza apenas setores em `UserProfile.setores_permitidos`
- **Restrição rígida:** não consegue acessar dados de outras unidades/setores

---

## 4. Checklist de Deploy

- [ ] Atualizar código no servidor
- [ ] Executar migrações: `python manage.py migrate accounts`
- [ ] Configurar worker de tarefas (systemd/supervisor/cron)
- [ ] Testar importação/exportação assíncrona
- [ ] Verificar logs: `tail -f logs/django.log`
- [ ] Monitorar tarefas no admin: `/admin/core/taskqueue/`
- [ ] Validar permissões de Liderança

---

## 5. Breaking Changes

### 5.1. AdminRequiredMixin Removido
**Se você usava:**
```python
from apps.core.mixins import AdminRequiredMixin

class MinhaView(AdminRequiredMixin, View):
    pass
```

**Agora use:**
```python
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

@method_decorator(staff_member_required, name='dispatch')
class MinhaView(View):
    pass
```

Ou simplesmente permita que superusers acessem através de `RHRequiredMixin` ou `DashboardAccessMixin`.

### 5.2. Importações agora são assíncronas
- ImportCSVView agora enfileira tarefas ao invés de processar imediatamente
- Usuários recebem mensagem "enfileirado com sucesso" ao invés de "importado com sucesso"
- Processamento acontece em background via worker

---

## 6. Troubleshooting

### Worker não está processando tarefas

**Verificar se worker está rodando:**
```bash
# Systemd
sudo systemctl status vivamente-queue-worker

# Processos
ps aux | grep process_task_queue
```

**Verificar logs:**
```bash
tail -f logs/django.log
```

**Processar manualmente:**
```bash
python manage.py process_task_queue
```

### Tarefas ficam em status 'failed'

**Ver erro:**
```python
from apps.core.models import TaskQueue

failed_tasks = TaskQueue.objects.filter(status='failed').order_by('-created_at')[:5]
for task in failed_tasks:
    print(f"Task {task.id}: {task.error_message}")
```

**Retry manual:**
```python
task = TaskQueue.objects.get(id=123)
task.status = 'pending'
task.attempts = 0
task.error_message = ''
task.save()
```

### Performance do banco de dados

**Limpar tarefas antigas:**
```python
from django.utils import timezone
from datetime import timedelta
from apps.core.models import TaskQueue

# Deletar tarefas concluídas com mais de 30 dias
old_date = timezone.now() - timedelta(days=30)
TaskQueue.objects.filter(
    status='completed',
    completed_at__lt=old_date
).delete()
```

---

## 7. Rollback

### Se precisar voltar atrás:

```bash
# Reverter migração
python manage.py migrate accounts 0001_initial

# Reverter código
git revert <commit_hash>

# Parar worker
sudo systemctl stop vivamente-queue-worker
```

**ATENÇÃO:** Usuários convertidos para superuser permanecerão como superuser mesmo após o rollback da migração.

---

**Fim do Changelog**
