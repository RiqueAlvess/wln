/**
 * Editor TipTap para Plano de Ação
 * Biblioteca: TipTap (baseado em ProseMirror)
 */

import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableHeader from '@tiptap/extension-table-header'
import TableCell from '@tiptap/extension-table-cell'
import TextStyle from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'

class PlanoAcaoEditor {
    constructor(elementId, options = {}) {
        this.elementId = elementId;
        this.options = options;
        this.editor = null;
        this.autoSaveTimeout = null;
        this.init();
    }

    init() {
        const element = document.querySelector(`#${this.elementId}`);
        if (!element) {
            console.error(`Elemento #${this.elementId} não encontrado`);
            return;
        }

        // Obter conteúdo inicial do campo hidden
        const contentInput = document.querySelector('#id_conteudo_estruturado');
        let initialContent = '';

        if (contentInput && contentInput.value) {
            try {
                initialContent = JSON.parse(contentInput.value);
            } catch (e) {
                initialContent = '<p>Digite o plano de ação aqui...</p>';
            }
        } else {
            initialContent = this.getDefaultContent();
        }

        this.editor = new Editor({
            element: element,
            extensions: [
                StarterKit.configure({
                    heading: {
                        levels: [1, 2, 3]
                    }
                }),
                TaskList,
                TaskItem.configure({
                    nested: true,
                }),
                Table.configure({
                    resizable: true,
                }),
                TableRow,
                TableHeader,
                TableCell,
                TextStyle,
                Color,
            ],
            content: initialContent,
            editorProps: {
                attributes: {
                    class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none',
                },
            },
            onUpdate: ({ editor }) => {
                this.handleUpdate(editor);
            },
        });

        this.setupToolbar();
    }

    getDefaultContent() {
        return {
            type: 'doc',
            content: [
                {
                    type: 'heading',
                    attrs: { level: 2 },
                    content: [{ type: 'text', text: 'Objetivo' }]
                },
                {
                    type: 'paragraph',
                    content: [
                        { type: 'text', text: 'Descreva o objetivo principal do plano de ação...' }
                    ]
                },
                {
                    type: 'heading',
                    attrs: { level: 2 },
                    content: [{ type: 'text', text: 'Ações Propostas' }]
                },
                {
                    type: 'heading',
                    attrs: { level: 3 },
                    content: [{ type: 'text', text: 'Curto Prazo (30 dias)' }]
                },
                {
                    type: 'taskList',
                    content: [
                        {
                            type: 'taskItem',
                            attrs: { checked: false },
                            content: [
                                {
                                    type: 'paragraph',
                                    content: [{ type: 'text', text: 'Ação 1' }]
                                }
                            ]
                        },
                        {
                            type: 'taskItem',
                            attrs: { checked: false },
                            content: [
                                {
                                    type: 'paragraph',
                                    content: [{ type: 'text', text: 'Ação 2' }]
                                }
                            ]
                        }
                    ]
                },
                {
                    type: 'heading',
                    attrs: { level: 3 },
                    content: [{ type: 'text', text: 'Médio Prazo (90 dias)' }]
                },
                {
                    type: 'taskList',
                    content: [
                        {
                            type: 'taskItem',
                            attrs: { checked: false },
                            content: [
                                {
                                    type: 'paragraph',
                                    content: [{ type: 'text', text: 'Ação 1' }]
                                }
                            ]
                        }
                    ]
                },
                {
                    type: 'heading',
                    attrs: { level: 2 },
                    content: [{ type: 'text', text: 'Recursos Necessários' }]
                },
                {
                    type: 'bulletList',
                    content: [
                        {
                            type: 'listItem',
                            content: [
                                {
                                    type: 'paragraph',
                                    content: [
                                        { type: 'text', text: 'Orçamento: ', marks: [{ type: 'bold' }] },
                                        { type: 'text', text: 'R$ ...' }
                                    ]
                                }
                            ]
                        },
                        {
                            type: 'listItem',
                            content: [
                                {
                                    type: 'paragraph',
                                    content: [
                                        { type: 'text', text: 'Treinamento: ', marks: [{ type: 'bold' }] },
                                        { type: 'text', text: '...' }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    type: 'heading',
                    attrs: { level: 2 },
                    content: [{ type: 'text', text: 'Indicadores de Acompanhamento' }]
                },
                {
                    type: 'table',
                    content: [
                        {
                            type: 'tableRow',
                            content: [
                                {
                                    type: 'tableHeader',
                                    content: [
                                        {
                                            type: 'paragraph',
                                            content: [{ type: 'text', text: 'Indicador' }]
                                        }
                                    ]
                                },
                                {
                                    type: 'tableHeader',
                                    content: [
                                        {
                                            type: 'paragraph',
                                            content: [{ type: 'text', text: 'Meta' }]
                                        }
                                    ]
                                },
                                {
                                    type: 'tableHeader',
                                    content: [
                                        {
                                            type: 'paragraph',
                                            content: [{ type: 'text', text: 'Prazo' }]
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            type: 'tableRow',
                            content: [
                                {
                                    type: 'tableCell',
                                    content: [
                                        {
                                            type: 'paragraph',
                                            content: [{ type: 'text', text: '...' }]
                                        }
                                    ]
                                },
                                {
                                    type: 'tableCell',
                                    content: [
                                        {
                                            type: 'paragraph',
                                            content: [{ type: 'text', text: '...' }]
                                        }
                                    ]
                                },
                                {
                                    type: 'tableCell',
                                    content: [
                                        {
                                            type: 'paragraph',
                                            content: [{ type: 'text', text: '...' }]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        };
    }

    setupToolbar() {
        // Botões de formatação básica
        this.setupButton('btn-bold', () => this.editor.chain().focus().toggleBold().run());
        this.setupButton('btn-italic', () => this.editor.chain().focus().toggleItalic().run());
        this.setupButton('btn-underline', () => this.editor.chain().focus().toggleUnderline().run());
        this.setupButton('btn-strike', () => this.editor.chain().focus().toggleStrike().run());

        // Cabeçalhos
        this.setupButton('btn-h1', () => this.editor.chain().focus().toggleHeading({ level: 1 }).run());
        this.setupButton('btn-h2', () => this.editor.chain().focus().toggleHeading({ level: 2 }).run());
        this.setupButton('btn-h3', () => this.editor.chain().focus().toggleHeading({ level: 3 }).run());

        // Listas
        this.setupButton('btn-bullet-list', () => this.editor.chain().focus().toggleBulletList().run());
        this.setupButton('btn-ordered-list', () => this.editor.chain().focus().toggleOrderedList().run());
        this.setupButton('btn-task-list', () => this.editor.chain().focus().toggleTaskList().run());

        // Tabela
        this.setupButton('btn-table', () => {
            this.editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
        });
        this.setupButton('btn-add-row', () => this.editor.chain().focus().addRowAfter().run());
        this.setupButton('btn-add-col', () => this.editor.chain().focus().addColumnAfter().run());
        this.setupButton('btn-delete-row', () => this.editor.chain().focus().deleteRow().run());
        this.setupButton('btn-delete-col', () => this.editor.chain().focus().deleteColumn().run());
        this.setupButton('btn-delete-table', () => this.editor.chain().focus().deleteTable().run());

        // Color picker
        const colorPicker = document.querySelector('#color-picker');
        if (colorPicker) {
            colorPicker.addEventListener('change', (e) => {
                this.editor.chain().focus().setColor(e.target.value).run();
            });
        }
    }

    setupButton(id, callback) {
        const button = document.querySelector(`#${id}`);
        if (button) {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                callback();
            });
        }
    }

    handleUpdate(editor) {
        // Salvar JSON no campo hidden
        const contentInput = document.querySelector('#id_conteudo_estruturado');
        if (contentInput) {
            contentInput.value = JSON.stringify(editor.getJSON());
        }

        // Salvar HTML no campo hidden
        const htmlInput = document.querySelector('#id_conteudo_html');
        if (htmlInput) {
            htmlInput.value = editor.getHTML();
        }

        // Auto-save (debounced)
        if (this.options.autoSave) {
            clearTimeout(this.autoSaveTimeout);
            this.autoSaveTimeout = setTimeout(() => {
                this.autoSave();
            }, 2000);
        }
    }

    autoSave() {
        console.log('Auto-salvando conteúdo...');
        // Implementar lógica de auto-save via AJAX
        const form = document.querySelector('form');
        if (form && this.options.autoSaveUrl) {
            const formData = new FormData(form);

            fetch(this.options.autoSaveUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Conteúdo salvo automaticamente', data);
                this.showNotification('Rascunho salvo automaticamente', 'success');
            })
            .catch(error => {
                console.error('Erro ao salvar:', error);
            });
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showNotification(message, type = 'info') {
        // Implementar notificação toast
        console.log(`[${type}] ${message}`);
    }

    destroy() {
        if (this.editor) {
            this.editor.destroy();
        }
    }

    getJSON() {
        return this.editor ? this.editor.getJSON() : null;
    }

    getHTML() {
        return this.editor ? this.editor.getHTML() : '';
    }
}

// Exportar para uso global
window.PlanoAcaoEditor = PlanoAcaoEditor;

// Inicializar automaticamente se elemento existir
document.addEventListener('DOMContentLoaded', () => {
    const editorElement = document.querySelector('#editor-plano-acao');
    if (editorElement) {
        const autoSaveUrl = editorElement.dataset.autosaveUrl || '';
        window.editorInstance = new PlanoAcaoEditor('editor-plano-acao', {
            autoSave: true,
            autoSaveUrl: autoSaveUrl
        });
    }
});
