# Editor Rico para Plano de Ação - TipTap

## 📝 Visão Geral

Este documento descreve a implementação do Editor Rico WYSIWYG (What You See Is What You Get) para criação de Planos de Ação formatados no sistema Vivamente360.

### Biblioteca Utilizada
**TipTap** - Editor moderno baseado em ProseMirror
- Leve e extensível
- Suporte nativo a Markdown
- Totalmente compatível com Django
- Estrutura de dados JSON para persistência

---

## 🎯 Funcionalidades do Editor

### Formatação de Texto
- **Negrito**, *Itálico*, <u>Sublinhado</u>, ~~Tachado~~
- Cabeçalhos (H1, H2, H3)
- Cores de texto customizáveis

### Listas
- Listas com marcadores (bullet lists)
- Listas numeradas (ordered lists)
- **Task Lists** (listas de tarefas com checkboxes)

### Tabelas
- Inserção de tabelas
- Adicionar/remover linhas e colunas
- Cabeçalhos de tabela

### Estrutura de Conteúdo Padrão
O editor vem pré-configurado com uma estrutura sugerida:
```
## Objetivo
[Descrição do objetivo...]

## Ações Propostas
### Curto Prazo (30 dias)
☐ Ação 1
☐ Ação 2

### Médio Prazo (90 dias)
☐ Ação 1

## Recursos Necessários
• Orçamento: R$ ...
• Treinamento: ...

## Indicadores de Acompanhamento
| Indicador | Meta | Prazo |
|-----------|------|-------|
| ...       | ...  | ...   |
```

---

## 🏗️ Arquitetura Técnica

### Backend (Django)

#### Modelo de Dados
```python
# apps/actions/models.py
class PlanoAcao(TimeStampedModel):
    # Campos existentes...
    nivel_risco = models.CharField(max_length=20)
    responsavel = models.CharField(max_length=255)
    prazo = models.DateField()
    status = models.CharField(...)

    # NOVOS CAMPOS para editor rico
    conteudo_estruturado = models.JSONField(
        null=True,
        blank=True,
        help_text="Conteúdo do editor TipTap em formato JSON"
    )
    conteudo_html = models.TextField(
        blank=True,
        help_text="HTML renderizado do plano de ação para exportação"
    )

    # Campos legados (mantidos para compatibilidade)
    descricao_risco = models.TextField()
    acao_proposta = models.TextField()
    recursos_necessarios = models.TextField(blank=True)
    indicadores = models.TextField(blank=True)
```

#### Views Principais

**PlanoAcaoCreateView** - Criar novo plano de ação
- URL: `/actions/<campaign_id>/planos/novo/`
- Template: `actions/plano_acao_form.html`

**PlanoAcaoUpdateView** - Editar plano existente
- URL: `/actions/<campaign_id>/planos/<pk>/editar/`

**PlanoAcaoAutoSaveView** - Auto-save (AJAX)
- URL: `/actions/<campaign_id>/planos/<pk>/autosave/`
- Salva rascunhos a cada 2 segundos

**ExportPlanoAcaoRichWordView** - Exportar para DOCX
- URL: `/actions/<campaign_id>/planos/<pk>/export-docx/`
- Converte HTML → DOCX com formatação preservada

#### Serviço de Exportação
```python
# services/export_service.py
class ExportService:
    @staticmethod
    def export_plano_acao_rich_word(plano_acao):
        """
        Converte HTML do editor TipTap para DOCX
        Suporta:
        - Cabeçalhos (H1-H6)
        - Parágrafos formatados (negrito, itálico, etc.)
        - Listas (bullet, numbered, task)
        - Tabelas
        - Cores de texto
        """
```

---

### Frontend (JavaScript + TipTap)

#### Estrutura de Arquivos
```
vivamente360/
├── package.json                    # Dependências npm
├── webpack.config.js               # Build config
├── static/
│   ├── js/
│   │   ├── editor-plano-acao.js   # Componente principal
│   │   └── dist/
│   │       └── editor-plano-acao.bundle.js
│   └── css/
│       └── editor.css              # Estilos do editor
└── templates/
    └── actions/
        └── plano_acao_form.html    # Template do formulário
```

#### Componente JavaScript
```javascript
// static/js/editor-plano-acao.js
class PlanoAcaoEditor {
    constructor(elementId, options) {
        this.editor = new Editor({
            element: document.querySelector(`#${elementId}`),
            extensions: [
                StarterKit,
                TaskList,
                TaskItem,
                Table,
                TextStyle,
                Color
            ],
            content: initialContent,
            onUpdate: ({ editor }) => {
                this.handleUpdate(editor);
            }
        });
    }

    handleUpdate(editor) {
        // Salva JSON e HTML em campos hidden
        document.querySelector('#id_conteudo_estruturado').value =
            JSON.stringify(editor.getJSON());
        document.querySelector('#id_conteudo_html').value =
            editor.getHTML();

        // Auto-save debounced (2s)
        this.autoSave();
    }
}
```

---

## 🚀 Instalação e Configuração

### 1. Instalar Dependências NPM
```bash
cd vivamente360/
npm install
```

Isso instalará:
- @tiptap/core
- @tiptap/starter-kit
- @tiptap/extension-task-list
- @tiptap/extension-task-item
- @tiptap/extension-table
- @tiptap/extension-text-style
- @tiptap/extension-color
- webpack
- webpack-cli

### 2. Build do JavaScript
```bash
npm run dev
```

Ou para desenvolvimento com watch:
```bash
npm run watch
```

### 3. Instalar Dependências Python
```bash
pip install -r requirements.txt
```

Novas dependências adicionadas:
- `beautifulsoup4==4.12.3` - Parsing HTML
- `reportlab==4.0.9` - Geração de PDF

### 4. Aplicar Migrações
```bash
python manage.py migrate actions
```

---

## 📖 Como Usar

### Criar Novo Plano de Ação

1. Acesse a lista de planos de ação de uma campanha
2. Clique em "Novo Plano de Ação"
3. Preencha os campos básicos:
   - Dimensão
   - Nível de Risco
   - Responsável
   - Prazo
   - Status

4. Use o editor rico para criar o conteúdo detalhado:
   - Clique nos botões da toolbar para formatar texto
   - Use a estrutura sugerida ou crie sua própria
   - Adicione tabelas, listas de tarefas, etc.

5. O sistema salva automaticamente a cada 2 segundos
6. Clique em "Salvar Plano de Ação" para finalizar

### Exportar para Word (DOCX)

1. Na tela de edição do plano de ação:
   - Clique em "Exportar DOCX"
   - O documento será baixado com toda formatação preservada

2. Na lista de planos de ação:
   - Use o botão de exportação individual de cada plano

### Visualizar Preview

- Clique em "Visualizar" para ver como o plano ficará antes de salvar
- Modal mostra o HTML renderizado

---

## 🔧 Manutenção e Troubleshooting

### Problemas Comuns

**1. Editor não carrega**
- Verifique se o bundle JavaScript foi gerado: `static/js/dist/editor-plano-acao.bundle.js`
- Execute: `npm run dev`

**2. Auto-save não funciona**
- Verifique o console do browser para erros AJAX
- Confirme que a URL de autosave está correta
- Verifique o token CSRF

**3. Exportação DOCX com formatação incorreta**
- Verifique se beautifulsoup4 está instalado
- Teste o HTML gerado pelo editor

### Logs e Debug

```javascript
// Ativar logs no JavaScript
window.editorInstance.editor.on('update', ({ editor }) => {
    console.log('Editor atualizado:', editor.getJSON());
});
```

```python
# Debug no backend
from pprint import pprint
pprint(plano_acao.conteudo_estruturado)
```

---

## 🔄 Migração de Dados Legados

Para converter planos de ação antigos (campos de texto simples) para o novo formato rico:

```python
# Script de migração (a ser executado via Django shell)
from apps.actions.models import PlanoAcao

def migrate_legacy_planos():
    planos = PlanoAcao.objects.filter(conteudo_estruturado__isnull=True)

    for plano in planos:
        html = f"""
        <h2>Descrição do Risco</h2>
        <p>{plano.descricao_risco}</p>

        <h2>Ação Proposta</h2>
        <p>{plano.acao_proposta}</p>
        """

        if plano.recursos_necessarios:
            html += f"""
            <h2>Recursos Necessários</h2>
            <p>{plano.recursos_necessarios}</p>
            """

        if plano.indicadores:
            html += f"""
            <h2>Indicadores</h2>
            <p>{plano.indicadores}</p>
            """

        plano.conteudo_html = html
        # Gerar JSON a partir do HTML seria mais complexo
        # Por enquanto, manter campos legados preenchidos
        plano.save()

# Executar
migrate_legacy_planos()
```

---

## 📊 Estrutura de Dados JSON

Exemplo de `conteudo_estruturado`:
```json
{
  "type": "doc",
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Objetivo" }]
    },
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Reduzir demandas excessivas em ",
          "marks": []
        },
        {
          "type": "text",
          "text": "30 dias",
          "marks": [{ "type": "bold" }]
        }
      ]
    },
    {
      "type": "taskList",
      "content": [
        {
          "type": "taskItem",
          "attrs": { "checked": false },
          "content": [
            {
              "type": "paragraph",
              "content": [{ "type": "text", "text": "Contratar 2 auxiliares" }]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 🎨 Personalização do Editor

### Adicionar Nova Extensão

```javascript
// static/js/editor-plano-acao.js
import Highlight from '@tiptap/extension-highlight'

// Adicionar ao array de extensions:
extensions: [
    StarterKit,
    TaskList,
    TaskItem,
    Table,
    TextStyle,
    Color,
    Highlight,  // ← Nova extensão
]
```

### Customizar Toolbar

Edite `templates/actions/plano_acao_form.html`:
```html
<div class="editor-toolbar">
    <!-- Adicionar novo botão -->
    <button type="button" id="btn-highlight" title="Destacar">
        <i class="bi bi-highlighter"></i>
    </button>
</div>
```

E adicione o handler em `static/js/editor-plano-acao.js`:
```javascript
setupToolbar() {
    // ...
    this.setupButton('btn-highlight', () =>
        this.editor.chain().focus().toggleHighlight().run()
    );
}
```

---

## 📝 Checklist de Implementação

- [x] Criar modelo de dados com JSONField
- [x] Implementar forms com validação
- [x] Criar views (Create, Update, AutoSave)
- [x] Configurar rotas (URLs)
- [x] Desenvolver componente JavaScript TipTap
- [x] Estilizar editor (CSS)
- [x] Implementar exportação DOCX
- [x] Criar template do formulário
- [x] Configurar build (webpack)
- [x] Adicionar dependências (package.json, requirements.txt)
- [x] Criar migração do banco de dados
- [x] Documentar implementação

---

## 🔗 Referências

- [TipTap Documentation](https://tiptap.dev/)
- [ProseMirror](https://prosemirror.net/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

---

## 👥 Suporte

Para dúvidas ou problemas, consulte:
- Documentação técnica do projeto
- Logs do sistema (`logs/`)
- Console do navegador (F12)

---

**Versão:** 1.0
**Data:** 2026-01-30
**Autor:** Vivamente360 Development Team
