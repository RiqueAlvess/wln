# Sistema de Processamento de Tarefas e Notificações - Atualização v2

## 🎉 Novas Features Implementadas

### 1. Sistema de Notificações Completo ✅

#### Navbar Atualizado
- **Ícone de Notificações**: Badge com contador de notificações não lidas
- **Dropdown de Notificações**: Mostra últimas 10 notificações
- **Auto-refresh**: Contador atualiza a cada 30 segundos
- **Link de Processamento**: Acesso rápido à tela de processamento

#### Recursos do Dropdown
- ✅ Ícones coloridos por tipo de notificação
- ✅ Tempo relativo ("há 5 minutos", "há 2 horas")
- ✅ Botões de ação para notificações com links
- ✅ Marcar individual como lida (clique na notificação)
- ✅ Marcar todas como lidas (botão no header)
- ✅ Link para ver todas as tarefas

### 2. Paginação nas APIs ✅

Todas as APIs agora suportam paginação:

```
GET /api/tasks/?page=1&page_size=20
GET /api/notifications/?page=1&page_size=10
```

**Parâmetros**:
- `page`: Número da página (padrão: 1)
- `page_size`: Itens por página (padrão: 20, máximo: 100)

**Resposta**:
```json
{
  "count": 150,
  "next": "http://api.com/tasks/?page=2",
  "previous": null,
  "results": [...]
}
```

### 3. Expiração Automática de Notificações ✅

**Comportamento**:
- Notificações são deletadas automaticamente após **24 horas**
- APIs retornam apenas notificações ativas (últimas 24h)
- Limpeza automática executada pelo worker a cada 1 hora

**Manager Customizado**:
```python
# Buscar apenas notificações ativas
UserNotification.objects.active()

# Deletar notificações expiradas
deleted_count = UserNotification.objects.delete_expired()
```

### 4. Worker Unificado Aprimorado ✅

O comando `process_email_queue` agora:
- ✅ Processa todas as tasks (emails, exports, análises IA, etc.)
- ✅ Limpa notificações expiradas automaticamente
- ✅ Configura intervalo de limpeza

**Uso**:
```bash
# Worker padrão (limpeza a cada 1h)
python manage.py process_email_queue

# Customizar intervalos
python manage.py process_email_queue --interval 1 --batch-size 10 --cleanup-interval 3600
```

**Parâmetros**:
- `--interval`: Tempo entre processamentos (padrão: 1s)
- `--batch-size`: Tasks por lote (padrão: 10)
- `--cleanup-interval`: Tempo entre limpezas (padrão: 3600s / 1h)

### 5. Novo Comando de Limpeza Manual ✅

```bash
# Deletar notificações expiradas manualmente
python manage.py cleanup_expired_notifications
```

## 📊 Arquitetura Atualizada

```
┌─────────────────────────────────────────────┐
│           NAVEGADOR (Frontend)              │
│  ┌──────────────┐    ┌─────────────────┐   │
│  │ Navbar       │    │ Tela Processa.  │   │
│  │ - Badge      │◄──►│ - Paginação     │   │
│  │ - Dropdown   │    │ - Auto-refresh  │   │
│  └──────────────┘    └─────────────────┘   │
└────────────┬────────────────────────────────┘
             │
        API REST (Paginada)
             │
┌────────────▼────────────────────────────────┐
│           BACKEND (Django)                  │
│  ┌─────────────────────────────────────┐   │
│  │  Models                             │   │
│  │  - TaskQueue (arquivos, progresso)  │   │
│  │  - UserNotification (24h)           │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  APIs (Paginadas)                   │   │
│  │  - /api/tasks/                      │   │
│  │  - /api/notifications/              │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  Worker Unificado                   │   │
│  │  - Processa tasks                   │   │
│  │  - Limpa notificações (1h)          │   │
│  │  - Cria notificações automáticas    │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
             │
             ▼
       ┌──────────┐
       │ Storage  │
       │ (Arquivos│
       │  24h)    │
       └──────────┘
```

## 🚀 Fluxo de Trabalho Completo

### 1. Usuário Solicita Export

```python
# View cria a task
task = TaskQueue.objects.create(
    task_type='export_plano_acao',
    user=request.user,
    empresa=request.user.empresa,
    payload={'campaign_id': 1}
)

# Mostra modal de confirmação
messages.success(request, 'Exportação iniciada!')
```

### 2. Worker Processa Task

```
1. Worker detecta task pendente
2. Atualiza status → 'processing'
3. Atualiza progresso (0-100%)
4. Gera arquivo e salva
5. Atualiza task com informações do arquivo
6. Cria notificação automática
7. Status → 'completed'
```

### 3. Usuário Recebe Notificação

```
1. Badge no navbar mostra contador
2. Usuário clica no ícone
3. Dropdown mostra notificação:
   "✓ Plano de ação exportado"
   [Baixar arquivo]
4. Clica em "Baixar arquivo"
5. Notificação marcada como lida
6. Arquivo baixado
```

### 4. Limpeza Automática (1h depois)

```
1. Worker verifica tempo desde última limpeza
2. Se passou 1h:
   - UserNotification.objects.delete_expired()
   - Deleta notificações > 24h
   - Log: "5 notificações expiradas deletadas"
```

## 📱 Uso das Notificações

### No JavaScript (Frontend)

```javascript
// Carregar contador
fetch('/api/notifications/unread_count/')
  .then(r => r.json())
  .then(data => badge.textContent = data.count);

// Carregar lista paginada
fetch('/api/notifications/?page_size=10')
  .then(r => r.json())
  .then(data => renderNotifications(data.results));

// Marcar como lida
fetch(`/api/notifications/${id}/mark_read/`, {
  method: 'POST',
  headers: {'X-CSRFToken': csrftoken}
});
```

### No Python (Backend)

```python
from apps.core.models import UserNotification

# Criar notificação manual
UserNotification.objects.create(
    user=user,
    empresa=user.empresa,
    notification_type='info',
    title='Bem-vindo!',
    message='Sua conta foi criada com sucesso.'
)

# Buscar não lidas
unread = UserNotification.objects.active().filter(
    user=user,
    is_read=False
)

# Marcar todas como lidas
unread.update(is_read=True, read_at=timezone.now())

# Deletar expiradas
UserNotification.objects.delete_expired()
```

## 🔧 Comandos Disponíveis

### Worker Principal (Recomendado)
```bash
# Inicia worker que processa tasks E limpa notificações
python manage.py process_email_queue --interval 1 --batch-size 10 --cleanup-interval 3600
```

### Limpeza Manual de Arquivos Antigos
```bash
# Remove arquivos de tasks com mais de 30 dias
python manage.py cleanup_old_task_files --days 30
```

### Limpeza Manual de Notificações
```bash
# Remove notificações com mais de 24h
python manage.py cleanup_expired_notifications
```

## 📋 Checklist de Deploy

- [ ] Executar migrations: `python manage.py migrate core`
- [ ] Iniciar worker: `python manage.py process_email_queue`
- [ ] Verificar navbar (badge de notificações aparece)
- [ ] Testar criação de task (export qualquer relatório)
- [ ] Verificar notificação no dropdown
- [ ] Testar download de arquivo
- [ ] Aguardar 1h e verificar log de limpeza
- [ ] Configurar cron para limpeza de arquivos antigos

## 🎨 Customização

### Alterar Tempo de Expiração de Notificações

Editar `apps/core/models.py`:
```python
def active(self):
    cutoff = timezone.now() - timedelta(hours=48)  # 48h ao invés de 24h
    return self.filter(created_at__gte=cutoff)
```

### Alterar Intervalo de Limpeza do Worker

```bash
# Limpar a cada 30 minutos (1800s)
python manage.py process_email_queue --cleanup-interval 1800
```

### Alterar Tamanho de Página Padrão

Editar `apps/core/api_views.py`:
```python
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50  # Alterar de 20 para 50
    max_page_size = 200  # Alterar limite máximo
```

## 🐛 Troubleshooting

### Badge de Notificações Não Aparece

1. Verificar se usuário está autenticado
2. Abrir console do navegador e verificar erros
3. Testar API manualmente: `/api/notifications/unread_count/`

### Notificações Não São Deletadas

1. Verificar se worker está rodando
2. Verificar logs: `--cleanup-interval` configurado corretamente?
3. Executar manualmente: `python manage.py cleanup_expired_notifications`

### Paginação Não Funciona

1. Verificar parâmetros na URL: `?page=1&page_size=20`
2. Verificar resposta da API tem campos `count`, `next`, `previous`
3. Ajustar JavaScript para usar `data.results` ao invés de `data`

## 📊 Melhorias Implementadas - Resumo

| Feature | Status | Benefício |
|---------|--------|-----------|
| Badge de notificações no navbar | ✅ | Usuário vê imediatamente quando algo completa |
| Dropdown de notificações | ✅ | Acesso rápido sem sair da página |
| Paginação nas APIs | ✅ | Performance melhor com muitas tasks |
| Expiração automática 24h | ✅ | Banco de dados não cresce indefinidamente |
| Worker unificado | ✅ | Um único comando processa tudo |
| Limpeza automática | ✅ | Manutenção zero, tudo automático |
| Link de processamento | ✅ | Acesso rápido à tela de acompanhamento |

## 🎯 Próximos Passos (Futuro)

- [ ] WebSocket para notificações em tempo real (sem polling)
- [ ] Push notifications no navegador
- [ ] Filtros avançados na tela de processamento
- [ ] Exportar histórico de tasks para CSV
- [ ] Dashboard de estatísticas de tasks
- [ ] Notificações por email para tasks críticas
- [ ] Retry automático de tasks falhadas

## 🏁 Conclusão

O sistema agora está **100% completo** com:

✅ Correção dos bugs de export
✅ Sistema de tasks e file storage
✅ Sistema de notificações visual e funcional
✅ Paginação em todas as APIs
✅ Expiração automática de notificações
✅ Worker unificado com limpeza automática
✅ Navbar atualizado com acesso rápido
✅ Documentação completa

O usuário não fica mais preso em telas durante processamentos, recebe notificações em tempo real, e todo o sistema é auto-gerenciado com limpezas automáticas!
