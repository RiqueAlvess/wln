# Remover módulos de evidência, checklist e conformidade LGPD + Correções

## 📋 Resumo

Esta PR remove os módulos de evidência, checklist e conformidade LGPD conforme solicitado, além de corrigir erros no dashboard e configurar páginas de erro personalizadas.

## 🔧 Mudanças Principais

### 1. Correção de Bug no Dashboard ✅
**Arquivo:** `vivamente360/services/score_service.py`

- **Problema:** `TypeError: unsupported operand type(s) for +: 'int' and 'str'`
- **Solução:** Adicionado método `_to_int()` que converte valores de forma segura antes de somar
- **Impacto:** Dashboard agora funciona corretamente sem erros de tipo

### 2. Remoção do Módulo de Evidência 🗑️

**Modelos removidos:**
- `Evidencia` de `apps/actions/models.py`

**Views removidas:**
- `EvidenciaListView`
- `EvidenciaUploadView`
- `EvidenciaDeleteView`

**Arquivos deletados:**
- `apps/actions/forms.py`
- `templates/actions/evidencia_upload.html`
- `templates/actions/evidencias_list.html`

**URLs removidas:**
- `/actions/<campaign_id>/evidencias/`
- `/actions/<campaign_id>/evidencias/upload/`
- `/actions/evidencias/<pk>/delete/`

**Admin removido:**
- `EvidenciaAdmin`

### 3. Remoção do Módulo de Checklist 🗑️

**Modelos removidos:**
- `ChecklistEtapa` de `apps/actions/models.py`

**Views removidas:**
- `ChecklistView`

**Arquivos deletados:**
- `templates/actions/checklist.html`

**URLs removidas:**
- `/actions/<campaign_id>/checklist/`

**Admin removido:**
- `ChecklistEtapaAdmin`

### 4. Remoção do Módulo de Conformidade LGPD 🗑️

**Modelos removidos:**
- `LGPDComplianceItem` de `apps/core/models.py`

**Views removidas:**
- `LGPDComplianceView` de `apps/core/views.py`

**Arquivos deletados:**
- `templates/core/lgpd_compliance.html`
- `templates/survey/step_lgpd.html`
- `apps/core/management/commands/populate_lgpd.py`

**URLs removidas:**
- `/lgpd-compliance/`

**Menu atualizado:**
- Removido link "Conformidade LGPD" do `templates/base.html`

### 5. Limpeza de Referências nos Templates 🧹

**templates/dashboard/index.html:**
- Removido link para checklist de conformidade
- Substituído por texto genérico sobre planos de ação

**templates/campaigns/detail.html:**
- Removidos botões "Checklist" e "Evidências"
- Mantidos apenas: Gerenciar Convites, Dashboard e Planos de Ação

**templates/campaigns/list.html:**
- Removido botão de checklist da listagem
- Mantidos: Ver Detalhes, Gerenciar Convites e Planos de Ação

### 6. Migrações de Banco de Dados 📊

**Criadas:**
- `apps/actions/migrations/0002_remove_evidencia_checklist.py`
  - Remove modelo `Evidencia`
  - Remove modelo `ChecklistEtapa`

- `apps/core/migrations/0003_remove_lgpdcomplianceitem.py`
  - Remove modelo `LGPDComplianceItem`

### 7. Páginas de Erro Personalizadas 🎨

**Configuração:**
- Views de teste adicionadas em `apps/core/views.py`
- URLs de teste disponíveis em desenvolvimento:
  - `/test/404/` - Página não encontrada
  - `/test/500/` - Erro interno do servidor
  - `/test/403/` - Acesso negado
  - `/test/400/` - Requisição inválida

**Páginas já existentes e funcionais:**
- `templates/404.html`
- `templates/500.html`
- `templates/403.html`
- `templates/400.html`

## 📦 Arquivos Modificados

### Alterados:
- `vivamente360/services/score_service.py`
- `vivamente360/apps/actions/admin.py`
- `vivamente360/apps/actions/models.py`
- `vivamente360/apps/actions/urls.py`
- `vivamente360/apps/actions/views.py`
- `vivamente360/apps/core/models.py`
- `vivamente360/apps/core/urls.py`
- `vivamente360/apps/core/views.py`
- `vivamente360/templates/base.html`
- `vivamente360/templates/dashboard/index.html`
- `vivamente360/templates/campaigns/detail.html`
- `vivamente360/templates/campaigns/list.html`

### Criados:
- `vivamente360/apps/actions/migrations/0002_remove_evidencia_checklist.py`
- `vivamente360/apps/core/migrations/0003_remove_lgpdcomplianceitem.py`

### Deletados:
- `vivamente360/apps/actions/forms.py`
- `vivamente360/apps/core/management/commands/populate_lgpd.py`
- `vivamente360/templates/actions/checklist.html`
- `vivamente360/templates/actions/evidencia_upload.html`
- `vivamente360/templates/actions/evidencias_list.html`
- `vivamente360/templates/core/lgpd_compliance.html`
- `vivamente360/templates/survey/step_lgpd.html`

## 🧪 Como Testar

1. **Aplicar migrações:**
   ```bash
   cd vivamente360
   python manage.py migrate actions
   python manage.py migrate core
   ```

2. **Iniciar servidor:**
   ```bash
   python manage.py runserver
   ```

3. **Testar Dashboard:**
   - Acessar `/dashboard/` e selecionar uma campanha
   - Verificar que não há erros de `NoReverseMatch`
   - Confirmar que os cálculos de score funcionam

4. **Testar navegação:**
   - Acessar lista de campanhas
   - Verificar que botões de checklist e evidências foram removidos
   - Confirmar que botão "Planos de Ação" funciona

5. **Testar páginas de erro (desenvolvimento):**
   - Acessar `/test/404/` - deve mostrar página 404
   - Acessar `/test/500/` - deve mostrar página 500
   - Acessar rota inexistente - deve mostrar página 404 personalizada

## ⚠️ Breaking Changes

- **Modelos removidos:** `Evidencia`, `ChecklistEtapa`, `LGPDComplianceItem`
- **URLs removidas:** Todas URLs relacionadas a evidências, checklist e LGPD
- **Dados:** As migrações irão DELETAR as tabelas e seus dados do banco

## 📝 Notas Adicionais

- As páginas de erro personalizadas funcionam automaticamente em produção (DEBUG=False)
- Os templates de email que continham referências a "checklist" e "LGPD" foram mantidos por serem apenas CSS classes ou menções genéricas
- O módulo de Planos de Ação foi mantido e continua funcional

## ✅ Checklist

- [x] Código testado localmente
- [x] Migrações criadas
- [x] Referências removidas dos templates
- [x] URLs atualizadas
- [x] Admin atualizado
- [x] Páginas de erro configuradas
- [x] Commits com mensagens descritivas

---

**Branch:** `claude/remove-modules-nTJK1`
**Commits:**
- `ce825b8` fix: Corrigir TypeError no cálculo de score do dashboard
- `cb2d47b` feat: Remover módulos de evidência, checklist e conformidade LGPD
- `f071a83` fix: Remover referências aos módulos deletados e adicionar views de teste de erro

https://claude.ai/code/session_01SPMz12N8ooR96HziePRikC
