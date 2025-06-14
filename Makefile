# Docker settings
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_EXEC = $(DOCKER_COMPOSE) exec

# Container names
APP_CONTAINER = bot
POSTGRES_CONTAINER = postgres
REDIS_CONTAINER = redis_fsm

# Build Docker containers
.PHONY: build
build:
	$(DOCKER_COMPOSE) build

# Up Docker containers
.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d

# Run Docker containers
.PHONY: run
run:
	$(DOCKER_COMPOSE) up --build -d

# Stop the Docker containers
.PHONY: down
down:
	$(DOCKER_COMPOSE) down

.PHONY: deploy-prod
deploy-prod:
	make build && make down && make up && make migrate

.PHONY: deploy-dev
deploy-dev:
	make run && make migrate

# Restart containers
.PHONY: restart
restart:
	$(DOCKER_COMPOSE) restart

# Remove volumes and clean up
.PHONY: clean
clean:
	$(DOCKER_COMPOSE) down -v --rmi local --remove-orphans

# Remove builds and other unneeded stuff
.PHONY: clean-resources
clean-resources:
	docker image prune -f
	docker container prune -f
	docker builder prune -f

# Alembic: Create a new migration
.PHONY: migration
migration:
	$(DOCKER_COMPOSE_EXEC) $(APP_CONTAINER) alembic revision --autogenerate -m "$(message)"

# Alembic: Apply migrations
.PHONY: migrate
migrate:
	$(DOCKER_COMPOSE_EXEC) -T $(APP_CONTAINER) alembic upgrade head

# Execute a bash shell inside the app container
.PHONY: shell
shell:
	$(DOCKER_COMPOSE_EXEC) $(APP_CONTAINER) /bin/bash

# View logs for all services
.PHONY: logs
logs:
	$(DOCKER_COMPOSE) logs -f

# View logs for a specific service
.PHONY: logs-app
logs-app:
	$(DOCKER_COMPOSE) logs -f $(APP_CONTAINER)


.PHONY: logs-postgres
logs-postgres:
	$(DOCKER_COMPOSE) logs -f $(POSTGRES_CONTAINER)
