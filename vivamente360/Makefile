.PHONY: help setup install migrate run worker test shell superuser populate clean logs

PYTHON = python
MANAGE = $(PYTHON) manage.py
SETTINGS = --settings=config.settings.development

help:
	@echo "VIVAMENTE 360 - Comandos disponíveis:"
	@echo ""
	@echo "  make setup       - Configuração completa (install + migrate + populate)"
	@echo "  make install     - Instalar dependências Python"
	@echo "  make migrate     - Aplicar migrations do banco de dados"
	@echo "  make run         - Iniciar servidor de desenvolvimento"
	@echo "  make worker      - Iniciar worker de e-mails"
	@echo "  make test        - Executar testes"
	@echo "  make shell       - Abrir shell Django"
	@echo "  make superuser   - Criar superusuário"
	@echo "  make populate    - Popular dimensões HSE-IT"
	@echo "  make clean       - Limpar arquivos temporários"
	@echo "  make logs        - Exibir logs da aplicação"

setup: install migrate populate
	@echo ""
	@echo "Setup completo! Crie o superusuário com: make superuser"
	@echo "Depois inicie o servidor com: make run"

install:
	pip install -r requirements.txt

migrate:
	$(MANAGE) migrate $(SETTINGS)

run:
	$(MANAGE) runserver $(SETTINGS)

worker:
	$(MANAGE) process_email_queue $(SETTINGS)

test:
	$(MANAGE) test $(SETTINGS)

shell:
	$(MANAGE) shell $(SETTINGS)

superuser:
	$(MANAGE) createsuperuser $(SETTINGS)

populate:
	$(MANAGE) populate_hse $(SETTINGS)

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

logs:
	tail -f logs/django.log
