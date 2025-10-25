# Load environment variables from .env file if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo '$(BLUE)Available commands:$(NC)'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker-compose build

up: ## Start development server with hot reload
	@echo "$(GREEN)Starting development server...$(NC)"
	docker-compose up --build

down: ## Stop all containers
	@echo "$(BLUE)Stopping containers...$(NC)"
	docker-compose down

restart: ## Restart containers
	@echo "$(BLUE)Restarting containers...$(NC)"
	docker-compose down
	docker-compose up --build

logs: ## View container logs
	docker-compose logs -f app

shell: ## Open shell in running container
	docker-compose exec app /bin/bash

test: ## Run tests in container
	docker-compose exec app pytest tests/ -v

clean: ## Clean up Docker resources
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	docker-compose down -v --remove-orphans
	docker system prune -f

deploy: ## Deploy to Google Cloud Run
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		echo "Create .env file from .env.example and configure your GCP settings"; \
		echo "Run: cp .env.example .env"; \
		exit 1; \
	fi
	@if [ -z "$(GCP_PROJECT_ID)" ]; then \
		echo "$(RED)Error: GCP_PROJECT_ID not set in .env file$(NC)"; \
		echo "Please add GCP_PROJECT_ID=your-project-id to .env file"; \
		exit 1; \
	fi
	@echo "$(GREEN)Deploying to Cloud Run...$(NC)"
	@echo "Project: $(GCP_PROJECT_ID)"
	@echo "Region: $(GCP_REGION)"
	@echo "Service: $(CLOUD_RUN_SERVICE)"
	./deploy-cloud-run.sh

format: ## Format code with black and isort
	poetry run black .
	poetry run isort .

lint: ## Lint code with flake8
	poetry run flake8 app/ tests/

type-check: ## Type check with mypy
	poetry run mypy app/

docker-test: ## Build and test Docker image
	@echo "$(BLUE)Building and testing Docker image...$(NC)"
	@if [ ! -f firebase_key.json ]; then \
		echo "$(RED)Error: firebase_key.json not found$(NC)"; \
		echo "Please ensure firebase_key.json exists in the project root"; \
		exit 1; \
	fi
	docker build -t learnforge-backend-test .
	@echo "$(GREEN)Build successful!$(NC)"
	@echo "$(BLUE)Starting container...$(NC)"
	docker run --rm -d --name learnforge-test -p 8080:8080 \
		-v $(PWD)/firebase_key.json:/app/firebase_key.json:ro \
		-e FIREBASE_PROJECT_ID=test \
		-e GOOGLE_APPLICATION_CREDENTIALS=/app/firebase_key.json \
		learnforge-backend-test
	@echo "$(BLUE)Waiting for server to start...$(NC)"
	@sleep 10
	@echo "$(BLUE)Testing health endpoint...$(NC)"
	@if curl -f http://localhost:8080/api/health 2>/dev/null; then \
		echo "\n$(GREEN)Health check passed!$(NC)"; \
	else \
		echo "\n$(RED)Health check failed!$(NC)"; \
		echo "$(BLUE)Container logs:$(NC)"; \
		docker logs learnforge-test; \
	fi
	@docker stop learnforge-test 2>/dev/null || true

status: ## Show container status
	docker-compose ps

size: ## Show Docker image size
	@echo "$(BLUE)Docker images:$(NC)"
	docker images | grep learnforge || echo "No images found"

prune: ## Remove all unused Docker resources (careful!)
	@echo "$(BLUE)Pruning Docker system...$(NC)"
	docker system prune -a --volumes -f
