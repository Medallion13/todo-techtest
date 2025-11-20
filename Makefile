.PHONY: help install lint format test clean localstack-up localstack-down localstack-logs deploy destroy synth diff

# ==========================================
# VARIABLES
# ==========================================

PYTHON := poetry run python
PYTEST := poetry run pytest
RUFF := poetry run ruff
MYPY := poetry run mypy
CDK := cdklocal

# LocalStack
LOCALSTACK_ENDPOINT := http://localhost:4566
AWS_REGION := us-east-1

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ========================================
# INSTALACIÓN Y SETUP
# ========================================

install: ## Instalar todas las dependencias (Python + Node)
	poetry install --with dev,infra
	cd frontend && npm install

install-backend: ## Solo instalar dependencias Python
	poetry install --with dev,infra

install-frontend: ## Solo instalar dependencias Node
	cd frontend && npm install

# ========================================
# CALIDAD DE CÓDIGO
# ========================================

lint: ## Ejecutar linters (Ruff + Mypy)
	$(RUFF) check backend/ infrastructure/
	$(MYPY) backend/ infrastructure/

format: ## Formatear código con Ruff
	$(RUFF) format backend/ infrastructure/
	$(RUFF) check --fix backend/ infrastructure/

# ========================================
# TESTING
# ========================================

test: ## Ejecutar todos los tests (no coverage)
	$(PYTEST) -v

test-unit: ## Solo tests unitarios
	$(PYTEST) -v -m unit

test-integration: ## Solo tests de integración (requiere LocalStack)
	$(PYTEST) -v -m integration

test-coverage: ## Tests con reporte de cobertura detallado
	$(PYTEST) --cov=backend --cov-report=html --cov-report=term-missing
	@echo "Reporte HTML generado en: htmlcov/index.html"

test-watch: ## Ejecutar tests en modo watch
	$(PYTEST) -v --looponfail

# ========================================
# LOCALSTACK (Docker)
# ========================================

localstack-up: ## Iniciar LocalStack
	docker-compose up -d

localstack-down: ## Detener LocalStack (mantiene datos)
	docker-compose down

localstack-logs: ## Ver logs de LocalStack
	docker-compose logs -f localstack

localstack-reset: ## Destruir y recrear LocalStack
	docker-compose down -v
	docker run --rm -v $(PWD)/localstack_data:/data alpine sh -c "rm -rf /data/*"
	docker-compose up -d

localstack-status: ## Verificar status de servicios LocalStack
	@echo "Status de LocalStack:"
	@docker-compose ps
	@awslocal --endpoint-url=$(LOCALSTACK_ENDPOINT) dynamodb list-tables || echo "DynamoDB: No found"

# ========================================
# AWS CDK (Infraestructura)
# ========================================

synth: ## Sintetizar CloudFormation template
	cd infrastructure && $(CDK) synth

deploy: build-lambda localstack-up ## Desplegar stack a LocalStack
	@echo "Desplegando a LocalStack..."
	cd infrastructure && \
		CDK_DISABLE_LEGACY_EXPORT_WARNING=1 \
		CDK_DISABLE_NOTICES=true \
		$(CDK) bootstrap || true
	cd infrastructure && \
		CDK_DISABLE_LEGACY_EXPORT_WARNING=1 \
		CDK_DISABLE_NOTICES=true \
		$(CDK) deploy --all \
			--require-approval never \
			--outputs-file ../cdk-outputs.json
	@echo "Outputs guardados en: cdk-outputs.json"
	@cat cdk-outputs.json 2>/dev/null || echo "No se generó cdk-outputs.json"

destroy: ## Destruir stack de LocalStack
	@echo "Destruyendo stack"
	cd infrastructure && $(CDK) destroy --all --force --profile localstack

diff:  ## Ver cambios pendientes en infraestructura
	cd infrastructure && $(CDK) diff --profile localstack

list: ## Listar stacks desplegados
	cd infrastructure && $(CDK) list --profile localstack

# ========================================
# DESARROLLO
# ========================================

dev-frontend: ## Iniciar servidor de desarrollo React
	cd frontend && npm run dev

dev-backend: ## [PLACEHOLDER] Desarrollo backend local
	@echo "Para backend, usa: make deploy (LocalStack)"

# ========================================
# UTILIDADES
# ========================================

clean: ## Limpiar archivos temporales
	@echo "Limpiando archivos temporales"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "cdk.out" -exec rm -rf {} + 2>/dev/null || true
	rm -f cdk-outputs.json

setup: install localstack-up ## Setup completo del proyecto (primera vez)
	@echo ""
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║              	 SETUP COMPLETO                       ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Próximos pasos:"
	@echo "  1. Verifica .env (cp .env.example .env si no existe)"
	@echo "  2. Despliega infraestructura: make deploy"
	@echo "  3. Verifica deployment: make localstack-status"
	@echo ""

# ========================================
# AWS LOCAL (Helpers)
# ========================================

aws-tables: # Listar tablas DynamoDB
	awslocal dynamodb list-tables --endpoint-url=$(LOCALSTACK_ENDPOINT)

aws-lambdas: ## Listar funciones Lambda
	awslocal lambda list-functions --endpoint-url=$(LOCALSTACK_ENDPOINT) \
		--query 'Functions[*].[FunctionName,Runtime,Handler]' --output table

aws-apis: ## Listar APIs Gateway
	awslocal apigateway get-rest-apis --endpoint-url=$(LOCALSTACK_ENDPOINT) \
		--query 'items[*].[name,id]' --output table

# ========================================
# VERSIONING
# ========================================

bump: ## Incrementar versión automáticamente (commitizen)
	poetry run cz bump --changelog

version: ## Mostrar versión actual
	@poetry version -s


.PHONY: build-lambda
build-lambda:  ## Build Lambda package with dependencies
	@echo "Building Lambda bundle..."
	@rm -rf .build/bundle
	@mkdir -p .build/bundle
	@pip install \
		'aws-lambda-powertools[pydantic]==2.30.2' \
		pydantic==2.7.4 \
		-t .build/bundle \
		--upgrade \
		--quiet
	@cp -r backend/functions .build/bundle/
	@cp -r backend/models .build/bundle/
	@cp -r backend/shared .build/bundle/
	@echo "✅ Lambda bundle ready"
