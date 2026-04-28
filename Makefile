# Docker settings
APP_ENV_FILE ?=
DEV_ENV_FILE ?= .env
APP_ENV_FILE_ABS = $(abspath $(APP_ENV_FILE))
DEV_ENV_FILE_ABS = $(abspath $(DEV_ENV_FILE))
COMPOSE_BASE = infra/docker-compose.yml
COMPOSE_DEV = infra/docker-compose.override.yml
DOCKER_COMPOSE = APP_ENV_FILE=$(APP_ENV_FILE_ABS) docker compose --env-file $(APP_ENV_FILE) -f $(COMPOSE_BASE)
DOCKER_COMPOSE_DEV = APP_ENV_FILE=$(DEV_ENV_FILE_ABS) docker compose --env-file $(DEV_ENV_FILE) -f $(COMPOSE_BASE) -f $(COMPOSE_DEV)
DOCKER_COMPOSE_EXEC = $(DOCKER_COMPOSE) exec
DOCKER_COMPOSE_DEV_EXEC = $(DOCKER_COMPOSE_DEV) exec

# Container names
APP_CONTAINER = bot
POSTGRES_CONTAINER = postgres
REDIS_CONTAINER = redis_fsm

# Requirements management
REQ_DIR = infra/requirements
REQ_NAMES = base prod dev
REQ_DEV_TXT = $(REQ_DIR)/dev.txt
REQ_PROD_TXT = $(REQ_DIR)/prod.txt
REQ_COMPILE_IMAGE ?= python:3.13-slim-bookworm
REQ_COMPILE_PLATFORM ?= linux/amd64
REQ_COMPILE_USER = $(shell id -u):$(shell id -g)

.PHONY: require-env-file
require-env-file:
	@test -n "$(APP_ENV_FILE)" || (echo "APP_ENV_FILE is required. Example: APP_ENV_FILE=.env make run" && exit 1)
	@test -f "$(APP_ENV_FILE)" || (echo "APP_ENV_FILE does not exist: $(APP_ENV_FILE)" && exit 1)

.PHONY: require-dev-env-file
require-dev-env-file:
	@test -f "$(DEV_ENV_FILE)" || (echo "DEV_ENV_FILE does not exist: $(DEV_ENV_FILE). Example: cp .env.example .env" && exit 1)

# Build Docker containers
.PHONY: build
build: require-env-file
	$(DOCKER_COMPOSE) build

# Up Docker containers
.PHONY: up
up: require-env-file
	$(DOCKER_COMPOSE) up -d

# Run Docker containers
.PHONY: run
run: require-env-file
	$(DOCKER_COMPOSE) up --build -d

# Run Docker containers in development mode
.PHONY: run-dev
run-dev: require-dev-env-file
	$(DOCKER_COMPOSE_DEV) up --build -d

# Stop the Docker containers
.PHONY: down
down: require-env-file
	$(DOCKER_COMPOSE) down

.PHONY: deploy-prod
deploy-prod:
	$(MAKE) build && $(MAKE) down && $(MAKE) up && $(MAKE) migrate

.PHONY: deploy-dev
deploy-dev:
	$(MAKE) run-dev && $(MAKE) APP_ENV_FILE=$(DEV_ENV_FILE) migrate

# Restart containers
.PHONY: restart
restart: require-env-file
	$(DOCKER_COMPOSE) restart

# Remove volumes and clean up
.PHONY: clean
clean: require-env-file
	$(DOCKER_COMPOSE) down -v --rmi local --remove-orphans

# Remove builds and other unneeded stuff
.PHONY: clean-resources
clean-resources:
	docker image prune -f
	docker container prune -f
	docker builder prune -f

# Alembic: Create a new migration in the dev image, where formatting tools exist.
.PHONY: migration
migration: require-dev-env-file
	$(DOCKER_COMPOSE_DEV_EXEC) $(APP_CONTAINER) alembic revision --autogenerate -m "$(message)"

# Alembic: Apply migrations
.PHONY: migrate
migrate: require-env-file
	$(DOCKER_COMPOSE_EXEC) -T $(APP_CONTAINER) alembic upgrade head

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: test
test:
	TESTING=true pytest

.PHONY: test-cov
test-cov:
	TESTING=true pytest \
		--cov=main \
		--cov=config_data \
		--cov=db \
		--cov=handlers \
		--cov=keyboards \
		--cov=lexicon \
		--cov=loggers \
		--cov=middlewares \
		--cov=services \
		--cov=states \
		--cov=utils \
		--cov-report=term-missing \
		--cov-report=xml

.PHONY: test-unit
test-unit:
	TESTING=true pytest tests/unit -v

.PHONY: test-integration
test-integration:
	TESTING=true pytest tests/integration -v

.PHONY: req-compile
req-compile:
	docker run --rm --platform=$(REQ_COMPILE_PLATFORM) \
		-e HOME=/tmp \
		-u $(REQ_COMPILE_USER) \
		-v $(CURDIR):/app \
		-w /app \
		$(REQ_COMPILE_IMAGE) \
		sh -lc 'set -e; python -m pip install --user --no-cache-dir --upgrade pip pip-tools && python scripts/sort_requirements_in.py $(addprefix $(REQ_DIR)/,$(addsuffix .in,$(REQ_NAMES))) && cd $(REQ_DIR) && for name in $(REQ_NAMES); do python -m piptools compile "$${name}.in" -o "$${name}.txt"; done'

.PHONY: req-sync-dev
req-sync-dev:
	python -m piptools sync $(REQ_DEV_TXT)

.PHONY: req-sync-prod
req-sync-prod:
	python -m piptools sync $(REQ_PROD_TXT)

# Execute a bash shell inside the app container
.PHONY: shell
shell: require-env-file
	$(DOCKER_COMPOSE_EXEC) $(APP_CONTAINER) /bin/bash

# View logs for all services
.PHONY: logs
logs: require-env-file
	$(DOCKER_COMPOSE) logs -f

# View logs for a specific service
.PHONY: logs-app
logs-app: require-env-file
	$(DOCKER_COMPOSE) logs -f $(APP_CONTAINER)

.PHONY: logs-postgres
logs-postgres: require-env-file
	$(DOCKER_COMPOSE) logs -f $(POSTGRES_CONTAINER)
