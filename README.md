# EngFlowBot

![CI](https://github.com/darkweid/EngFlowBot/actions/workflows/ci.yml/badge.svg?branch=main)
[![Coverage Status](https://coveralls.io/repos/github/darkweid/EngFlowBot/badge.svg?branch=main)](https://coveralls.io/github/darkweid/EngFlowBot?branch=main)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Aiogram](https://img.shields.io/badge/aiogram-3-blue)
![License](https://img.shields.io/github/license/darkweid/EngFlowBot)

EngFlowBot is a Telegram bot for Russian-speaking English learners. It combines
vocabulary practice, micro grammar tests, personal reminders, user progress, and
admin tools for managing learning content directly from Telegram.

## Key Features

For learners:

- **Vocabulary training** — spaced repetition with built-in rules, learning
  guidance, and per-user progress tracking
- **Topic word sets** — section and topic selection for adding new words to study
- **Hard mode** — optional self-check before multiple-choice vocabulary practice
- **Micro grammar tests** — section-based exercises with instant feedback,
  answer reveal, progress reset, and retake flows
- **Pronunciation links** — one-tap jump to Youglish examples
- **Stats dashboard** — today, active, learned, accuracy, and per-topic
  vocabulary metrics
- **Personal reminders** — notifications at the user's selected time and time zone

For admins:

- **Content management** — CRUD tools for word sections, vocabulary exercises,
  and grammar tests
- **User management** — user lookup, profile details, and account deletion tools
- **Personal word assignments** — add, review, and remove individual words for a
  selected user
- **Activity statistics** — daily, weekly, and monthly user activity
- **Broadcasts** — schedule admin messages and clear pending broadcasts
- **Event alerts** — startup, shutdown, sign-up, word-set, and test-completion
  notifications

## Bot Flows

Learner flow:

- Register with `/start` and choose a reminder time zone when prompted.
- Add topic word sets, practice due vocabulary, and optionally enable hard mode.
- Choose grammar test sections and subsections, reveal answers when needed, and
  retake completed tests after resetting progress.
- Review personal stats with activity and vocabulary progress metrics.

Admin flow:

- Open `/admin` to manage vocabulary content, grammar tests, and word sections.
- Look up users, review profile details, delete accounts, and manage personal
  word assignments.
- Schedule broadcasts, clear pending broadcasts, and monitor activity periods.
- Receive operational and user-activity alerts in the configured admin chat.

## Bot Commands

| Command | Audience | Purpose |
|---|---|---|
| `/start` | Users | Register a new user or return an existing user to the main menu. |
| `/main_menu` | Users | Open the main menu for registered users. |
| `/stats` | Users | Show profile and activity stats for today, week, or month. |
| `/reminder` | Users | View, change, or disable reminder settings. |
| `/info` | Users | Show bot rules and owner contact information. |
| `/admin` | Admins | Open the admin panel for content, users, activity, and broadcasts. |
| `/reset_fsm` | Utility | Clear the current FSM state for the current chat. |

## Architecture

```text
┌─────────────────────┐
│ Telegram API        │
└──────────┬──────────┘
           │
   aiogram.Dispatcher  ←  update middlewares
           │
┌──────────▼──────────┐
│  Handlers layer     │  ↔ DI via ServicesMiddleware
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Services layer     │  business logic
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Repositories layer  │  SQLAlchemy 2
└──────────┬──────────┘
           │
   PostgreSQL / Redis

```

Core boundaries:

- Handlers coordinate Telegram interaction and delegate persistence through
  injected services.
- Services own business logic and keep persistence details out of handlers.
- Repositories own SQLAlchemy query construction and return ORM models, scalars,
  or lightweight DTO-style data.
- Middlewares provide service dependency injection and centralized error
  handling.

Runtime code lives under `bot/`:

- `bot/main.py` creates the bot, dispatcher, middleware, routers, scheduler, and
  startup/shutdown hooks.
- `bot/handlers/` coordinates Telegram messages, callbacks, FSM state,
  keyboards, and service calls.
- `bot/services/` contains business logic.
- `bot/db/models.py` and `bot/db/repositories/` contain SQLAlchemy models and
  persistence access.
- `bot/middlewares/services.py` injects services and repositories into handler
  data.
- `bot/middlewares/errors.py` centralizes Telegram, validation, database, and
  unexpected error handling.
- `bot/lexicon/` stores user-facing Russian text.
- `bot/keyboards/` builds bot keyboards.
- `bot/states/` defines FSM states.
- `bot/utils/` contains shared scheduling, bot initialization, messaging, URL,
  parsing, and formatting helpers.
- `migrations/versions/` stores Alembic migrations.
- `infra/` stores Docker, Compose, and pinned dependency files.

## Stack

- Python 3.13
- Aiogram 3
- PostgreSQL 15
- Redis 7
- SQLAlchemy async
- Alembic
- APScheduler
- Pytest
- Ruff, Black, pre-commit
- Docker Compose

## Quick Start

Prerequisites:

- Docker and Docker Compose.
- Python 3.13 for local tooling and tests.
- A Telegram bot token from BotFather.

First run:

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Fill the Telegram token, admin IDs, database credentials, Redis DSN, and
   owner metadata in `.env`.

3. Start the development stack:

   ```bash
   make run-dev
   ```

4. Apply migrations inside the app container:

   ```bash
   APP_ENV_FILE=.env make migrate
   ```

5. View logs:

   ```bash
   make logs
   make logs-app
   ```

The first local run starts containers before migrations are applied. Run
`APP_ENV_FILE=.env make migrate` after the stack is up.

Stop the stack:

```bash
APP_ENV_FILE=.env make down
```

## Production-Style Run

Build and start the production image with Compose:

```bash
APP_ENV_FILE=.env make run
```

Apply migrations:

```bash
APP_ENV_FILE=.env make migrate
```

Restart containers:

```bash
APP_ENV_FILE=.env make restart
```

Remove containers, volumes, networks, local images, and orphans:

```bash
APP_ENV_FILE=.env make clean
```

## Testing

Run the full test suite:

```bash
make test
```

Run tests with coverage and create `coverage.xml`:

```bash
make test-cov
```

Run focused suites:

```bash
make test-unit
make test-integration
```

Run the CI syntax check locally:

```bash
python -m compileall bot tests
```

Tests live under `tests/`. Unit tests mirror application modules under
`tests/unit/`; integration tests live under `tests/integration/`; shared helpers,
factories, and fakes live under `tests/helpers/`, `tests/factories/`, and
`tests/fakes/`.


## Tooling

Run all pre-commit hooks:

```bash
make lint
```

Install local development dependencies:

```bash
python -m pip install -r infra/requirements/dev.txt
```

Regenerate pinned requirements from `infra/requirements/*.in`:

```bash
make req-compile
```

Sync a local environment to the dev or prod lock file:

```bash
make req-sync-dev
make req-sync-prod
```

## Configuration

The bot reads settings through Pydantic from environment variables. For local
development, copy `.env.example` to `.env`.

Important variables:

| Variable | Purpose | Format / example |
|---|---|---|
| `BOT_TOKEN` | Telegram bot token. | `1234567890:replace-with-bot-token` |
| `ADMIN_IDS` | Telegram admin IDs allowed to use `/admin`. | `[123456789]` |
| `REDIS_DSN` | Redis DSN for aiogram FSM storage. | `redis://redis_fsm` |
| `POSTGRES_USER` | PostgreSQL username. | `admin` |
| `POSTGRES_PASSWORD` | PostgreSQL password. | `password` |
| `POSTGRES_HOST` | PostgreSQL host visible to the app container. | `postgres` |
| `POSTGRES_PORT` | PostgreSQL port. | `5432` |
| `POSTGRES_DB` | PostgreSQL database name. | `postgres` |
| `DB_ECHO` | SQLAlchemy SQL echo flag. | `False` |
| `LOG_LEVEL` | Console log level. | `DEBUG` |
| `LOG_LEVEL_FILE` | File log level. | `WARNING` |
| `OWNER_NAME` | Owner display name shown in bot text. | `Ivan Ivanov` |
| `OWNER_TG_LINK` | Owner Telegram link shown in bot text. | `https://t.me/example` |
| `DEVELOPER_TG_ID` | Developer/admin Telegram ID for service messages. | `123456789` |

Do not commit real `.env` files, tokens, credentials, admin IDs, or Telegram user
data.

## CI/CD

GitHub Actions CI runs on pushes and pull requests to `main`.

CI currently checks:

- Python module compilation for `bot` and `tests`.
- Alembic migration heads.
- pre-commit hooks through `make lint`.
- pytest with coverage through `make test-cov`.
- Coveralls upload from `coverage.xml`.
- Docker image build from `infra/docker/Dockerfile`.

Server prerequisites for deploy:

- A Linux deploy user with access to Docker.
- A writable application directory, by default `/srv/engflowbot`.
- An SSH key whose public half is authorized for the deploy user.
- GitHub Secrets configured for SSH access and the production environment file.

Deployment is handled by `.github/workflows/deploy.yml` after a successful CI run
on `main`. The deploy job connects to the server over SSH, updates
`/srv/engflowbot`, uploads the environment file from GitHub Secrets, and runs:

```bash
APP_ENV_FILE="$REMOTE_ENV_FILE" make deploy-prod
```

Required deploy secrets:

- `SSH_PRIVATE_KEY`
- `SERVER_IP`
- `SSH_USER`
- `ENV_FILE`

## Useful Make Targets

- `make run-dev` - start the development Compose stack with override.
- `make run` - build and start the production-style Compose stack.
- `make migrate` - apply Alembic migrations in the app container.
- `make migration message="..."` - create an autogenerated Alembic revision.
- `make logs` / `make logs-app` / `make logs-postgres` - stream logs.
- `make test` / `make test-cov` - run tests.
- `make lint` - run pre-commit.
- `make req-compile` - regenerate pinned requirements.
- `make clean` - remove Compose resources.
