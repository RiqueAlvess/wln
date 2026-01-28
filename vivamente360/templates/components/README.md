# Componentes de Template

Este diretório contém componentes reutilizáveis que podem ser incluídos em outros templates.

## Modal de Erro (`error_modal.html`)

Modal genérico para exibir erros ao usuário de forma amigável.

### Uso Automático

O modal é **automaticamente incluído** em todas as páginas que estendem `base.html`. Ele intercepta:
- Erros JavaScript não tratados
- Rejeições de Promise não tratadas
- Erros de requisições AJAX/Fetch

### Uso Manual via JavaScript

```javascript
// Exibir modal de erro com mensagem padrão
showErrorModal();

// Exibir modal com mensagem personalizada
showErrorModal('Título Personalizado', 'Sua mensagem de erro aqui');

// Exibir modal apenas com mensagem (usa título padrão)
showErrorModal(null, 'Sua mensagem de erro');
```

### Uso em Requisições AJAX

```javascript
// Fetch API
fetch('/api/endpoint')
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na requisição');
        }
        return response.json();
    })
    .catch(error => {
        handleAjaxError(error); // Exibe o modal automaticamente
    });

// jQuery Ajax
$.ajax({
    url: '/api/endpoint',
    method: 'POST',
    data: { ... },
    success: function(data) {
        // Processar resposta
    },
    error: function(xhr, status, error) {
        handleAjaxError(new Error(error));
    }
});
```

### Personalização

O modal pode ser personalizado editando:
- **Visual**: Edite `/templates/components/error_modal.html` para alterar o design
- **Comportamento**: Modifique as funções JavaScript no mesmo arquivo
- **Mensagens padrão**: Altere os textos dentro dos elementos `#errorModalTitle` e `#errorModalMessage`

### Boas Práticas

1. **Use títulos descritivos**: `showErrorModal('Erro ao Salvar', 'Não foi possível salvar os dados')`
2. **Evite detalhes técnicos**: Usuários não precisam ver stack traces
3. **Ofereça soluções**: Indique o que o usuário pode fazer
4. **Log no console**: Erros também são logados no console para debug

### Exemplos Práticos

```javascript
// Erro de validação de formulário
if (!validateForm()) {
    showErrorModal(
        'Dados Inválidos',
        'Por favor, preencha todos os campos obrigatórios.'
    );
    return;
}

// Erro de permissão
if (!hasPermission) {
    showErrorModal(
        'Acesso Negado',
        'Você não tem permissão para realizar esta ação.'
    );
}

// Erro genérico de API
fetch('/api/data')
    .catch(error => {
        showErrorModal(
            'Erro de Conexão',
            'Não foi possível conectar ao servidor. Verifique sua conexão.'
        );
    });
```

### Desabilitar Interceptação Automática

Se você quiser desabilitar a interceptação automática de erros em uma página específica:

```javascript
// Remover listener de erros globais
window.removeEventListener('error', window.errorHandler);
window.removeEventListener('unhandledrejection', window.rejectionHandler);
```

## Adicionando Novos Componentes

Para adicionar novos componentes:

1. Crie o arquivo HTML neste diretório
2. Inclua no `base.html` ou em páginas específicas: `{% include 'components/seu_componente.html' %}`
3. Documente o uso neste README
