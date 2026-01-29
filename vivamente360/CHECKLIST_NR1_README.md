# Checklist de Compliance NR-1

## Visão Geral

Sistema completo de gerenciamento de checklist de compliance NR-1 para campanhas de avaliação de riscos psicossociais. Permite acompanhar as 6 etapas obrigatórias da NR-1, anexar evidências e exportar relatórios.

## Funcionalidades Implementadas

### 1. Modelos de Dados

#### ChecklistNR1Etapa
- **6 Etapas NR-1:**
  1. Preparação
  2. Identificação de Perigos
  3. Avaliação de Riscos
  4. Planejamento e Controle
  5. Monitoramento e Revisão
  6. Comunicação e Cultura

- **Campos:**
  - `etapa`: Número da etapa (1-6)
  - `item_texto`: Descrição da tarefa
  - `item_ordem`: Ordem do item dentro da etapa
  - `concluido`: Status de conclusão
  - `data_conclusao`: Data/hora de conclusão
  - `responsavel`: Nome do responsável
  - `prazo`: Data limite
  - `observacoes`: Observações adicionais
  - `automatico`: Flag para itens preenchidos automaticamente

#### EvidenciaNR1
- **Tipos de Evidências Suportados:**
  - Documento (PDF, DOC, DOCX)
  - Imagem (JPG, PNG)
  - Planilha (XLS, XLSX, CSV)
  - Apresentação (PPT, PPTX)
  - E-mail/Comunicado
  - Ata de Reunião
  - Certificado/Treinamento
  - Outro

- **Validações:**
  - Tamanho máximo: 10MB por arquivo
  - Tipos de arquivo permitidos por categoria
  - Upload seguro com validação de extensão

### 2. Interface Web

#### Página Principal (`/actions/<campaign_id>/checklist-nr1/`)
- Barra de progresso geral do checklist
- Visualização por etapas (expansível/retrátil)
- Checkboxes para marcar conclusão de itens
- Campos inline para responsável e prazo
- Área de observações expansível
- Contador de evidências por item
- Indicadores visuais de progresso

#### Upload de Evidências
- Modal interativo para upload
- Drag & drop de arquivos
- Preview de arquivo selecionado
- Seleção de tipo de evidência
- Campo de descrição opcional
- Validação em tempo real

#### Funcionalidades JavaScript
- Atualização AJAX sem reload de página
- Validação de formulários
- Preview de arquivos
- Confirmação de deleção
- Feedback visual de ações

### 3. API REST

#### Endpoints de Checklist

**GET/POST/PUT/DELETE** `/actions/api/checklist-nr1/`
- CRUD completo de itens do checklist
- Filtros: `campaign`, `empresa`, `etapa`, `concluido`
- Ordenação: `etapa`, `item_ordem`, `prazo`, `updated_at`

**GET** `/actions/api/checklist-nr1/resumo/?campaign_id=<id>`
- Resumo completo do checklist
- Progresso geral e por etapa
- Contadores de itens concluídos

**POST** `/actions/api/checklist-nr1/<id>/marcar_concluido/`
- Marcar item como concluído/não concluído
- Atualização automática de `data_conclusao`

**POST** `/actions/api/checklist-nr1/criar_padrao/`
- Cria checklist padrão NR-1 para uma campanha
- 24 itens distribuídos nas 6 etapas
- Itens automáticos já vêm marcados como concluídos

#### Endpoints de Evidências

**GET/POST/DELETE** `/actions/api/evidencias-nr1/`
- CRUD de evidências
- Upload multipart/form-data
- Filtros: `checklist_item`, `campaign`, `empresa`, `tipo`
- Metadata automático: tamanho, extensão, uploader

### 4. Exportação

#### PDF (`/actions/<campaign_id>/checklist-nr1/export-pdf/`)
- Relatório completo em PDF
- Informações da campanha
- Progresso geral e por etapa
- Tabelas detalhadas de todos os itens
- Status, responsáveis, prazos e evidências
- Seção de assinaturas (SST, RH, Diretor)

#### Formato do PDF
- Layout A4 profissional
- Cores e estilos consistentes
- Tabelas com grid
- Paginação automática
- Marca d'água da campanha

### 5. Django Admin

#### ChecklistNR1EtapaAdmin
- Listagem com filtros avançados
- Busca por texto do item, responsável, observações
- Hierarquia de datas por prazo
- Organização por etapas
- Campos agrupados em fieldsets

#### EvidenciaNR1Admin
- Listagem com preview de metadados
- Filtros por tipo, empresa, campanha
- Busca por nome de arquivo e descrição
- Visualização de tamanho formatado
- Link para item do checklist relacionado

## Como Usar

### 1. Criar Checklist para uma Campanha

#### Via API (Recomendado)
```bash
curl -X POST http://localhost:8000/actions/api/checklist-nr1/criar_padrao/ \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": 1}'
```

#### Via Django Admin
1. Acesse `/admin/actions/checklistnr1etapa/`
2. Clique em "Adicionar item de checklist NR-1"
3. Preencha os campos obrigatórios
4. Salve

### 2. Acessar Interface Web
1. Acesse `/actions/<campaign_id>/checklist-nr1/`
2. Visualize o progresso geral
3. Expanda as etapas desejadas
4. Marque itens como concluídos
5. Adicione responsáveis e prazos
6. Faça upload de evidências

### 3. Upload de Evidências
1. Clique em "Adicionar" na coluna Evidências
2. Selecione o tipo de evidência
3. Adicione descrição (opcional)
4. Arraste o arquivo ou clique para selecionar
5. Clique em "Enviar Evidência"

### 4. Exportar Relatório
1. Na página do checklist, clique em "Exportar PDF"
2. O PDF será baixado automaticamente
3. Arquivo nomeado como `checklist_nr1_<nome_campanha>.pdf`

## Itens Padrão do Checklist

### Etapa 1: Preparação (5 itens)
1. Definir equipe responsável pela avaliação
2. Comunicar colaboradores sobre a pesquisa
3. Garantir anonimato e confidencialidade
4. Selecionar instrumento de avaliação (HSE-IT) ✓ Automático
5. Definir cronograma de aplicação

### Etapa 2: Identificação de Perigos (4 itens)
1. Mapear setores e cargos da empresa
2. Identificar fatores de risco por área
3. Levantar histórico de afastamentos
4. Consultar PCMSO e ASO existentes

### Etapa 3: Avaliação de Riscos (4 itens)
1. Aplicar questionário HSE-IT ✓ Automático
2. Calcular scores por dimensão ✓ Automático
3. Classificar níveis de risco (Matriz P×S)
4. Priorizar áreas de intervenção

### Etapa 4: Planejamento e Controle (4 itens)
1. Elaborar planos de ação para riscos críticos
2. Definir responsáveis e prazos
3. Alocar recursos necessários
4. Estabelecer indicadores de acompanhamento

### Etapa 5: Monitoramento e Revisão (4 itens)
1. Acompanhar execução dos planos de ação
2. Reavaliar riscos periodicamente
3. Revisar eficácia das intervenções
4. Ajustar estratégias conforme necessário

### Etapa 6: Comunicação e Cultura (4 itens)
1. Divulgar resultados aos colaboradores
2. Promover treinamentos sobre saúde mental
3. Fortalecer canais de comunicação interna
4. Fomentar cultura de prevenção e bem-estar

## Arquivos Criados/Modificados

### Novos Arquivos
- `apps/actions/serializers.py` - Serializers REST
- `apps/actions/migrations/0003_add_checklist_nr1_evidencia_nr1.py` - Migração
- `templates/actions/checklist_nr1.html` - Interface web
- `CHECKLIST_NR1_README.md` - Esta documentação

### Arquivos Modificados
- `apps/actions/models.py` - Adicionados ChecklistNR1Etapa e EvidenciaNR1
- `apps/actions/views.py` - Adicionadas views e viewsets
- `apps/actions/urls.py` - Adicionadas rotas
- `apps/actions/admin.py` - Registrados novos modelos
- `services/export_service.py` - Adicionado método export_checklist_nr1_pdf

## Próximos Passos

### Melhorias Sugeridas
1. **Notificações:**
   - Email quando prazo se aproxima
   - Alerta para itens pendentes
   - Notificação de conclusão de etapa

2. **Relatórios Avançados:**
   - Gráficos de progresso ao longo do tempo
   - Comparação entre campanhas
   - Análise de tempo médio por etapa

3. **Automações:**
   - Integração com PCMSO/ASO externos
   - Importação de dados históricos
   - Geração automática de planos de ação

4. **Validações:**
   - Regras de negócio para ordem de conclusão
   - Validação de documentos obrigatórios
   - Checklist de aprovação por níveis

5. **Mobile:**
   - Interface responsiva otimizada
   - Upload via câmera do smartphone
   - Assinatura digital

## Suporte

Para dúvidas ou problemas:
- Verifique os logs do Django
- Consulte a documentação da API REST
- Revise as migrações do banco de dados

## Licença

Propriedade de Vivamente 360º - Sistema de Gestão de Riscos Psicossociais
