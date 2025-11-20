.PHONY: help build-lambda deploy test lint clean bootstrap synth

AWS_PROFILE := todo-app
AWS_REGION := us-east-1

help:
	@echo "Comandos disponibles:"
	@echo "  build-lambda  - Empaquetar Lambda"
	@echo "  deploy        - Deploy a AWS"
	@echo "  test          - Ejecutar tests"
	@echo "  lint          - Linters"
	@echo "  clean         - Limpiar archivos temporales"

build-lambda:
	@echo "🔨 Building Lambda bundle (optimized)..."
	@rm -rf .build/bundle
	@mkdir -p .build/bundle
	@pip install \
		pydantic==2.7.4 \
		-t .build/bundle \
		--upgrade \
		--quiet
	@cp -r backend/functions .build/bundle/
	@cp -r backend/models .build/bundle/
	@cp -r backend/shared .build/bundle/
	@echo "✅ Lambda bundle ready (without Powertools - uses AWS Layer)"

deploy: build-lambda  ## Deploy to AWS
	@echo "Deploying to AWS ($(AWS_PROFILE))..."
	@cd infrastructure && \
		cdk deploy --require-approval never --outputs-file ../cdk-outputs.json
	@echo "Deploy complete"
	@cat cdk-outputs.json

bootstrap:  ## Bootstrap CDK (only first time)
	@echo "Bootstrapping CDK..."
	@cd infrastructure && cdk bootstrap
	@echo "Bootstrap complete"

synth:  ## Synthesize CloudFormation template
	@cd infrastructure && cdk synth

test:
	poetry run pytest -v

lint:
	poetry run ruff check backend/ infrastructure/
	poetry run mypy backend/ infrastructure/

clean:
	@echo "Cleaning..."
	@rm -rf .build
	@rm -rf cdk.out
	@rm -f cdk-outputs.json
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"
