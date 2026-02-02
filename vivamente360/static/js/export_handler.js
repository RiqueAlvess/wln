/**
 * Handler para exportações assíncronas
 * Intercepta cliques em links de exportação e mostra modal de status
 */

(function() {
    'use strict';

    /**
     * Intercepta um link de exportação e mostra toast de feedback
     * @param {Event} event - Evento de clique
     * @param {HTMLElement} link - Elemento do link clicado
     */
    function handleExportClick(event, link) {
        event.preventDefault();

        const url = link.href;
        const method = link.dataset.method || 'GET';

        // Mostrar toast de processamento
        if (window.showToast) {
            showToast(
                '<i class="bi bi-hourglass-split"></i> <strong>Processando exportação...</strong>',
                'info',
                3000
            );
        }

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
                    // Mostrar toast de sucesso ao invés de modal bloqueante
                    if (window.showToast) {
                        showToast(
                            `<strong>Exportação iniciada com sucesso!</strong><br>
                            Você receberá uma notificação quando o arquivo estiver pronto para download.
                            <br><small class="text-white-50">Disponível por 48 horas</small>`,
                            'success',
                            6000
                        );
                    } else {
                        alert(data.message || 'Exportação iniciada. Você será notificado quando estiver pronta.');
                    }
                } else {
                    throw new Error('Resposta inválida do servidor');
                }
            })
            .catch(error => {
                console.error('Erro ao processar exportação:', error);
                if (window.showToast) {
                    showToast(
                        `<i class="bi bi-x-circle"></i> <strong>Erro ao exportar</strong><br>${error.message || 'Ocorreu um erro ao iniciar a exportação. Por favor, tente novamente.'}`,
                        'error',
                        5000
                    );
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

        // Mostrar toast de processamento
        if (window.showToast) {
            showToast(
                '<i class="bi bi-hourglass-split"></i> <strong>Processando exportação...</strong>',
                'info',
                3000
            );
        }

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
                    // Mostrar toast de sucesso
                    if (window.showToast) {
                        showToast(
                            message || `<strong>Exportação iniciada com sucesso!</strong><br>
                            Você receberá uma notificação quando o arquivo estiver pronto para download.
                            <br><small class="text-white-50">Disponível por 48 horas</small>`,
                            'success',
                            6000
                        );
                    } else {
                        alert(data.message || 'Exportação iniciada.');
                    }
                } else {
                    throw new Error('Resposta inválida do servidor');
                }
            })
            .catch(error => {
                console.error('Erro ao processar exportação:', error);
                if (window.showToast) {
                    showToast(
                        `<i class="bi bi-x-circle"></i> <strong>Erro ao exportar</strong><br>${error.message}`,
                        'error',
                        5000
                    );
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
