# App de Artigos/Newsletter - Vivamente 360º

## Visão Geral

Este app implementa a funcionalidade de Central de Conhecimento do sistema Vivamente 360º, permitindo que administradores publiquem artigos educativos sobre NR-1, saúde mental, gestão de pessoas e outros tópicos relevantes.

## Características

### Modelo de Dados

**Artigo** (`apps/articles/models.py`):
- **Informações Básicas**:
  - `titulo`: Título do artigo (max 255 caracteres)
  - `slug`: URL amigável (gerado automaticamente)
  - `resumo`: Texto de prévia (max 500 caracteres)
  - `conteudo`: Conteúdo completo (suporta Markdown)
  - `imagem_capa`: Imagem principal (upload_to='artigos/%Y/%m/')

- **Autoria e Status**:
  - `autor`: ForeignKey para User
  - `status`: draft, published, archived
  - `publicado_em`: Data/hora de publicação
  - `destaque`: Boolean para artigo em destaque

- **Categorização**:
  - `categoria`: nr1, saude, gestao, dicas, casos, novidades

- **Métricas**:
  - `visualizacoes`: Contador de visualizações
  - `created_at`, `updated_at`: Timestamps (TimeStampedModel)

### Funcionalidades

#### 1. Listagem de Artigos (`/artigos/`)
- Exibe artigo em destaque no topo
- Grid de artigos recentes
- Filtro por categoria
- Busca por título/resumo/conteúdo
- Paginação (12 artigos por página)
- Sidebar com artigos mais lidos

#### 2. Detalhamento de Artigo (`/artigos/<slug>/`)
- Visualização completa do conteúdo
- Incremento automático de visualizações
- Informações do autor
- Botões de compartilhamento social
- Artigos relacionados (mesma categoria)

#### 3. Painel Administrativo
- CRUD completo de artigos
- Filtros por status, categoria, data
- Actions em lote:
  - Publicar artigos
  - Arquivar artigos
  - Marcar/desmarcar destaque
- Auto-geração de slug
- Badge coloridos para categorias

### Arquitetura

```
apps/articles/
├── models.py          # Modelo Artigo
├── views.py           # ArtigoListView, ArtigoDetailView
├── urls.py            # Rotas do app
├── admin.py           # Configuração do admin
├── apps.py            # Configuração do app
└── migrations/        # Migrações do banco

app_selectors/
└── article_selectors.py  # Lógica de consultas

templates/articles/
├── artigo_list.html   # Página de listagem
└── artigo_detail.html # Página de detalhamento
```

### URLs

- **Listagem**: `/artigos/`
- **Filtro por categoria**: `/artigos/?categoria=nr1`
- **Busca**: `/artigos/?q=termo`
- **Detalhamento**: `/artigos/<slug>/`

### Selectors (app_selectors/article_selectors.py)

- `get_publicados()`: Retorna todos artigos publicados
- `get_destaque()`: Retorna artigo em destaque mais recente
- `get_recentes(limit=6)`: Retorna artigos recentes (excluindo destaque)
- `get_por_categoria(categoria)`: Filtra por categoria
- `get_by_slug(slug)`: Busca por slug
- `buscar(query)`: Busca fulltext
- `get_relacionados(artigo, limit=3)`: Artigos da mesma categoria
- `get_categorias_disponiveis()`: Categorias com artigos
- `get_mais_visualizados(limit=5)`: Artigos mais lidos

### Permissões

- **Visualização**: Todos os usuários autenticados (via `LoginRequiredMixin` e `DashboardAccessMixin`)
- **Criação/Edição**: Apenas administradores (via Django Admin)

### Integrações

1. **Bootstrap 5**: Layout responsivo
2. **Bootstrap Icons**: Ícones visuais
3. **Jinja2**: Templates
4. **Pillow**: Processamento de imagens

## Como Usar

### 1. Aplicar Migrações

```bash
python manage.py migrate
```

### 2. Criar Artigo via Admin

1. Acesse `/admin/`
2. Navegue para "Artigos"
3. Clique em "Adicionar Artigo"
4. Preencha os campos:
   - Título, Resumo, Conteúdo
   - Categoria
   - Upload de imagem (opcional)
   - Marque "Em Destaque" se desejar
5. Altere status para "Publicado"
6. Salve

### 3. Visualizar Artigos

- Acesse `/artigos/` ou clique em "Artigos" no menu superior
- Navegue pelos artigos e categorias
- Clique em um artigo para ler o conteúdo completo

## Melhorias Futuras

### Fase 2 - Engajamento
- [ ] Sistema de comentários
- [ ] Reações (útil/não útil)
- [ ] Newsletter por e-mail
- [ ] Tags adicionais
- [ ] SEO metadata

### Fase 3 - Analytics
- [ ] Dashboard de métricas
- [ ] Tempo médio de leitura
- [ ] Taxa de engajamento
- [ ] Artigos mais compartilhados

### Fase 4 - Conteúdo Avançado
- [ ] Markdown rendering avançado
- [ ] Syntax highlighting para código
- [ ] Embeds (YouTube, Twitter, etc.)
- [ ] Galeria de imagens
- [ ] PDFs anexos

## Dependências

- Django 5.0+
- Pillow (processamento de imagens)
- PostgreSQL (banco de dados)

## Testes

```bash
# Executar testes do app
python manage.py test apps.articles

# Verificar cobertura
coverage run --source='apps.articles' manage.py test apps.articles
coverage report
```

## Troubleshooting

### Imagens não aparecem

1. Verifique se `MEDIA_URL` e `MEDIA_ROOT` estão configurados em `settings.py`
2. Em desenvolvimento, certifique-se que `settings.DEBUG=True` e as rotas de media estão configuradas em `urls.py`

### Slug duplicado

O modelo gera automaticamente slugs únicos adicionando um sufixo numérico se necessário.

### Artigos não aparecem

1. Verifique se o status é "published"
2. Verifique se `publicado_em` é anterior à data atual
3. Verifique se o usuário está autenticado

## Suporte

Para dúvidas ou problemas, abra uma issue no repositório ou entre em contato com a equipe de desenvolvimento.
