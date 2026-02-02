/**
 * Handler para exportações assíncronas
 * Intercepta cliques em links de exportação e mostra modal de status
 */

(function() {
    'use strict';

    /**
     * Intercepta um link de exportação e mostra o modal de status
     * @param {Event} event - Evento de clique
     * @param {HTMLElement} link - Elemento do link clicado
     */
    function handleExportClick(event, link) {
        event.preventDefault();

        const url = link.href;
        const method = link.dataset.method || 'GET';

        // Fazer requisição para iniciar exportação
        const fetchOptions = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        // Adicionar CSRF token se for POST
        if (method === 'POST') {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (csrfToken) {
                fetchOptions.headers['X-CSRFToken'] = csrfToken;
            }
        }

        fetch(url, fetchOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao iniciar exportação');
                }
                return response.json();
            })
            .then(data => {
                if (data.task_id) {
                    // Mostrar modal com status da tarefa
                    if (window.ExportStatusManager) {
                        window.ExportStatusManager.show(data.task_id, data.message);
                    } else {
                        console.error('ExportStatusManager não está disponível');
                        alert(data.message || 'Exportação iniciada. Você será notificado quando estiver pronta.');
                    }
                } else {
                    throw new Error('Resposta inválida do servidor');
                }
            })
            .catch(error => {
                console.error('Erro ao processar exportação:', error);
                if (window.showErrorModal) {
                    window.showErrorModal('Erro ao Exportar', error.message || 'Ocorreu um erro ao iniciar a exportação. Por favor, tente novamente.');
                } else {
                    alert('Erro ao iniciar exportação: ' + error.message);
                }
            });
    }

    /**
     * Converte um link normal em um link de exportação assíncrona
     * @param {HTMLElement} link - Elemento do link
     */
    function setupExportLink(link) {
        link.addEventListener('click', function(event) {
            handleExportClick(event, link);
        });
    }

    /**
     * Inicializa todos os links de exportação assíncrona na página
     */
    function initExportLinks() {
        // Selecionar todos os links com a classe .async-export
        const exportLinks = document.querySelectorAll('a.async-export');

        exportLinks.forEach(function(link) {
            setupExportLink(link);
        });
    }

    /**
     * API pública para converter um link em exportação assíncrona
     */
    window.makeAsyncExport = function(selector) {
        const links = document.querySelectorAll(selector);
        links.forEach(function(link) {
            // Adicionar classe para indicar que é assíncrono
            link.classList.add('async-export');
            setupExportLink(link);
        });
    };

    /**
     * Função para iniciar uma exportação manualmente via JavaScript
     * @param {string} url - URL da exportação
     * @param {string} method - Método HTTP (GET ou POST)
     * @param {string} message - Mensagem customizada (opcional)
     */
    window.startAsyncExport = function(url, method, message) {
        method = method || 'GET';

        const fetchOptions = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (method === 'POST') {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (csrfToken) {
                fetchOptions.headers['X-CSRFToken'] = csrfToken;
            }
        }

        fetch(url, fetchOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao iniciar exportação');
                }
                return response.json();
            })
            .then(data => {
                if (data.task_id) {
                    if (window.ExportStatusManager) {
                        window.ExportStatusManager.show(data.task_id, message || data.message);
                    } else {
                        console.error('ExportStatusManager não está disponível');
                        alert(data.message || 'Exportação iniciada.');
                    }
                } else {
                    throw new Error('Resposta inválida do servidor');
                }
            })
            .catch(error => {
                console.error('Erro ao processar exportação:', error);
                if (window.showErrorModal) {
                    window.showErrorModal('Erro ao Exportar', error.message);
                } else {
                    alert('Erro: ' + error.message);
                }
            });
    };

    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initExportLinks);
    } else {
        initExportLinks();
    }

    // Observar mudanças no DOM para inicializar novos links dinamicamente
    if (window.MutationObserver) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    initExportLinks();
                }
            });
        });

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            });
        } else {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }
})();
