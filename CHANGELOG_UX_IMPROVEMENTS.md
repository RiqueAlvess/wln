# Melhorias de UX - Sistema VIVAMENTE 360º

## Resumo das Alterações

Este documento descreve as melhorias implementadas para resolver problemas críticos de UX no sistema VIVAMENTE 360º, especialmente relacionados a exportações e notificações.

## Data da Implementação

**Data**: 2026-02-02

## Problemas Resolvidos

### 1. Exportações redirecionando para JSON ❌ → ✅

**Problema**: Ao clicar em botões de exportação, o usuário era redirecionado para uma página mostrando JSON bruto ao invés de ver um modal de progresso.

**Solução**:
- Incluído modal de status de exportação (`export_status_modal.html`) globalmente no `base.html`
- Incluído script `export_handler.js` globalmente para interceptar links com classe `async-export`
- Corrigido template `checklist_nr1.html` para usar classe `async-export` nos botões de exportação
- Refatorada view `ChecklistNR1ExportPDFView` para usar fila de processamento assíncrono

### 2. Sistema de Notificações ✅

**Status**: O sistema de notificações já estava funcionando corretamente no backend (API em `apps/core/api_views.py`). Nenhuma alteração foi necessária.

### 3. Limpeza Automática de Arquivos Exportados 🆕

**Problema**: Arquivos exportados acumulavam indefinidamente no servidor.

**Solução**:
- Criado novo model `ExportedFile` com TTL de 48 horas
- Criado comando Django `cleanup_expired_exports` para remover arquivos expirados
- Adicionada interface administrativa para gerenciar arquivos exportados

---

## Arquivos Modificados

### Templates

1. **`templates/base.html`**
   - ✅ Incluído `{% include 'components/export_status_modal.html' %}`
   - ✅ Incluído `<script src="{{ static('js/export_handler.js') }}"></script>`

2. **`templates/actions/checklist_nr1.html`**
   - ✅ Botão "Exportar PDF" agora usa classe `async-export`
   - ✅ Removida função JavaScript `exportarPDF()` obsoleta
   - ✅ Botão "Gerar Relatório Completo" marcado como "em desenvolvimento"

### Views

3. **`apps/actions/views.py`**
   - ✅ Adicionado import de `logging`
   - ✅ Refatorada `ChecklistNR1ExportPDFView` para usar `TaskQueue` (fila assíncrona)
   - ✅ View agora retorna JSON com `task_id` e `status_url`

### Models

4. **`apps/core/models.py`**
   - ✅ Criado novo model `ExportedFile` com:
     - TTL de 48 horas (`expires_at`)
     - Rastreamento de downloads (`download_count`, `downloaded_at`)
     - Status (`pending`, `processing`, `completed`, `failed`, `expired`)
     - Tipo de arquivo (`excel`, `pdf`, `word`, `txt`)

### Migrations

5. **`apps/core/migrations/0005_add_exportedfile_model.py`**
   - ✅ Criada migration para o model `ExportedFile`
   - ✅ Criados índices para otimização de queries:
     - `(user, status, expires_at)`
     - `(status, expires_at)`
     - `(empresa, status)`

### Management Commands

6. **`apps/core/management/commands/cleanup_expired_exports.py`**
   - ✅ Comando para remover arquivos expirados (> 48h)
   - ✅ Suporta modo `--dry-run` para simulação
   - ✅ Suporta modo `--force` para limpeza forçada (> 30 dias)
   - ✅ Remove também tasks antigas sem `ExportedFile` associado (> 7 dias)

### Admin

7. **`apps/core/admin.py`**
   - ✅ Adicionada interface administrativa para `ExportedFile`
   - ✅ Badges coloridos para tipo e status
   - ✅ Ações administrativas:
     - Marcar como expirado
     - Deletar arquivos expirados do disco

---

## Recursos Já Existentes (Não Modificados)

### ✅ Funcionando Corretamente

1. **Modal de Status de Exportação**
   - Arquivo: `templates/components/export_status_modal.html`
   - JavaScript: `ExportStatusManager` embutido no modal
   - Polling automático a cada 2 segundos
   - Exibe progresso com barra de porcentagem
   - Mostra mensagens de sucesso/erro

2. **Handler de Exportações**
   - Arquivo: `static/js/export_handler.js`
   - Intercepta cliques em links com classe `async-export`
   - Faz requisição assíncrona e exibe modal
   - Suporta métodos GET e POST

3. **API de Tasks**
   - Endpoint: `/api/tasks/<task_id>/`
   - ViewSet: `TaskQueueViewSet` em `apps/core/api_views.py`
   - Retorna status, progresso, e URL de download

4. **API de Notificações**
   - Endpoint: `/api/notifications/`
   - Endpoints disponíveis:
     - `GET /api/notifications/` - Lista paginada
     - `GET /api/notifications/unread/` - Apenas não lidas
     - `GET /api/notifications/unread_count/` - Contador
     - `POST /api/notifications/mark_all_read/` - Marcar todas como lidas
     - `POST /api/notifications/<id>/mark_read/` - Marcar individual
   - JavaScript no `base.html` atualiza contador a cada 30 segundos

5. **Exportações Já Assíncronas**
   - ✅ `psychosocial_risk_matrix.html` - Exportar Excel e PGR
   - ✅ `plano_acao_list.html` - Exportar Word
   - ✅ `ExportRiskMatrixExcelView`
   - ✅ `ExportRiskMatrixPGRView`
   - ✅ `ExportPlanoAcaoWordView`
   - ✅ `ExportCampaignComparisonView`

---

## Como Usar

### Para Desenvolvedores

#### 1. Executar Migrations

```bash
python manage.py migrate core
```

#### 2. Configurar Cron Job para Limpeza Automática

Adicione ao crontab para executar diariamente:

```bash
# Executar diariamente às 2h da manhã
0 2 * * * cd /path/to/vivamente360 && python manage.py cleanup_expired_exports
```

Ou via systemd timer, supervisor, ou celery beat.

#### 3. Testar Comando de Limpeza

```bash
# Modo simulação (não deleta nada)
python manage.py cleanup_expired_exports --dry-run

# Limpeza normal (apenas expirados > 48h)
python manage.py cleanup_expired_exports

# Limpeza forçada (> 30 dias)
python manage.py cleanup_expired_exports --force
```

### Para Adicionar Novas Exportações

Para adicionar uma nova exportação assíncrona:

1. **Criar View que retorna JSON**:
```python
def get(self, request, *args, **kwargs):
    from apps.core.models import TaskQueue

    task = TaskQueue.objects.create(
        task_type='meu_tipo_exportacao',
        payload={'data': 'exemplo'},
        user=request.user,
        empresa=request.user.empresa
    )

    return JsonResponse({
        'task_id': task.id,
        'message': 'Exportação iniciada...',
        'status_url': f'/api/tasks/{task.id}/'
    })
```

2. **Adicionar link no template com classe `async-export`**:
```html
<a href="{% url 'minha_exportacao' %}" class="btn btn-primary async-export">
    <i class="bi bi-download"></i> Exportar
</a>
```

3. **(Opcional) Criar ExportedFile ao processar**:
```python
from datetime import timedelta
from django.utils import timezone
from apps.core.models import ExportedFile

# Ao criar a task
exported_file = ExportedFile.objects.create(
    task=task,
    user=request.user,
    empresa=request.user.empresa,
    tipo='excel',  # ou 'pdf', 'word', 'txt'
    expires_at=timezone.now() + timedelta(hours=48)
)
```

---

## Impacto nos Usuários

### Antes ❌
- Clique em "Exportar Excel" → Redirecionamento para página JSON
- Usuário não sabe se exportação foi iniciada
- Arquivos acumulam indefinidamente
- Sem feedback visual

### Depois ✅
- Clique em "Exportar Excel" → Modal aparece instantaneamente
- Barra de progresso mostra processamento
- Notificação quando arquivo está pronto
- Arquivo disponível por 48 horas
- Limpeza automática libera espaço

---

## Checklist de Verificação

### Frontend
- ✅ Modal de status incluído no `base.html`
- ✅ Script `export_handler.js` incluído no `base.html`
- ✅ Links de exportação com classe `async-export`
- ✅ Botões desabilitados mostram "em desenvolvimento"

### Backend
- ✅ Views de exportação retornam JSON com `task_id`
- ✅ Model `ExportedFile` criado
- ✅ Migration criada
- ✅ Admin interface configurada
- ✅ Comando de limpeza criado

### Testes Recomendados
- ⚠️ Testar exportação Excel no dashboard
- ⚠️ Testar exportação PDF do checklist NR-1
- ⚠️ Testar exportação Word de planos de ação
- ⚠️ Verificar sistema de notificações
- ⚠️ Executar comando de limpeza em modo dry-run
- ⚠️ Verificar se modal aparece corretamente
- ⚠️ Verificar se progresso é atualizado

---

## Próximos Passos (Opcional)

### Melhorias Futuras

1. **Página de Exportações do Usuário**
   - Listar todos os arquivos exportados
   - Mostrar data de expiração
   - Permitir re-download

2. **WebSockets para Notificações em Tempo Real**
   - Substituir polling por WebSockets
   - Notificações instantâneas
   - Melhor performance

3. **Estatísticas de Uso**
   - Tipos de exportação mais usados
   - Tempo médio de processamento
   - Taxa de downloads

4. **Compressão de Arquivos**
   - Comprimir arquivos grandes automaticamente
   - Economizar espaço em disco

---

## Suporte

Para dúvidas ou problemas:
1. Verificar logs: `/var/log/vivamente360/`
2. Verificar admin: `/admin/core/exportedfile/`
3. Executar diagnóstico: `python manage.py cleanup_expired_exports --dry-run`

---

## Referências

- **Código Original**: PR anterior implementou base do sistema de tasks
- **Documentação Django**: https://docs.djangoproject.com/
- **Bootstrap 5**: https://getbootstrap.com/docs/5.3/
- **Chart.js**: https://www.chartjs.org/

---

**Autor**: Claude AI
**Data**: 2026-02-02
**Versão**: 1.0
**Branch**: `claude/fix-vivamente-ux-issues-2z0UU`
