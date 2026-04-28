
## About EngFlowBot
**EngFlowBot** is an open-source Telegram bot that helps Russian-speaking learners master English through spaced-repetition vocabulary drills and micro-grammar tests.

| |                                                        |
|---|--------------------------------------------------------|
| **Stack** | Python 3.13 · Aiogram 3 · PostgreSQL 15 · Redis 7       |
| **License** | MIT                                                    |
| **Status** | ![CI](https://img.shields.io/badge/build-passing-brightgreen) |

---

### Learner highlights
* **📚 Spaced repetition** — adaptive intervals, optional *Hard mode*
* **🗣 Pronunciation links** — one-tap jump to Youglish examples
* **📝 Micro grammar tests** — instant feedback & per-topic progress
* **⏰ Personal reminders** — cron-like notifications in local time
* **📊 Stats dashboard** — today / active / learned / accuracy %

### Teacher / admin toolkit
* CRUD word sets & grammar tests directly in chat
* Per-student dashboards & deletion
* Global usage metrics (daily new words / tests / users)
* Broadcast scheduler
* Instant alerts (bot start/stop, sign-ups, word additions, test results)

---

### Architecture at a glance
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
│  Services layer     │  business logic, pure async
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Repositories layer  │  SQLAlchemy 2 (async)
└──────────┬──────────┘
           │
   PostgreSQL / Redis

```
---

### Cloning the Repository

1. Open your terminal.
2. Clone the repository:

   ```bash
   git clone https://github.com/darkweid/EngFlowBot.git
   cd EngFlowBot
   ```

3. Copy the example environment file to create your own:

   ```bash
   cp .env.example .env
   ```

4. Open the `.env` file in your favorite editor and configure the required environment variables.

### Running the Project

The project uses Docker Compose to orchestrate all services, including the Bot app, PostgreSQL, Redis. Docker and Compose files live in `infra/`; use the provided Makefile to simplify the workflow.

#### Building & Starting the Containers

By following these instructions and using the provided Makefile, you can easily deploy and manage the entire project stack with a few simple commands. Happy coding!

To build the Docker images (if needed) and run all containers in detached mode, use:

```bash
APP_ENV_FILE=.env make run
```

This command will:
- Build the images as necessary.
- Start all services defined in `infra/docker-compose.yml`.

For local development with the dev image and source bind mount:

```bash
make run-dev
```

By default `run-dev` uses the local `.env` file. To use another file, pass `DEV_ENV_FILE=path/to/.env`.

#### Dependencies

Requirements are split into base, production, and development inputs under `infra/requirements/`.
Compiled lock files are generated inside Docker:

```bash
make req-compile
```

Install the local development lock file:

```bash
python -m pip install -r infra/requirements/dev.txt
```

#### Viewing Logs

To view logs for all services:

```bash
make logs
```

To view logs for a specific service, such as the Bot app:

```bash
make logs-app
```


#### Stopping and Cleaning Up

- To stop all running containers:

  ```bash
  APP_ENV_FILE=.env make down
  ```

- To remove containers, networks, volumes, and local images (and clean up orphaned containers):

  ```bash
  APP_ENV_FILE=.env make clean
  ```

- To restart containers:

  ```bash
  APP_ENV_FILE=.env make restart
  ```
---

### Error handling

#### 1. Validation layer (ValueError)
	•	User message: “Wrong format.”
	•	Logs: level INFO with the error text.
	•	Side effects: none.

#### 2. Database layer (SQLAlchemyError)
	•	User message: “Database error. Please try again later.”
	•	Logs: full traceback at level ERROR.
	•	Alert: the traceback is forwarded to the developer chat via send_message_to_developer().

#### 3. Telegram rate-limit (TelegramRetryAfter)
	•	Action: bot sleeps for retry_after seconds, then re-runs the handler.
	•	Logs: level WARNING noting the cooldown.

#### 4. User blocked the bot (TelegramForbiddenError)
	•	User message: none (they have blocked the bot).
	•	Logs: level WARNING with the user ID.

#### 5. Bad request / impossible action (TelegramBadRequest)
	•	User message: “This action can’t be performed.”
	•	Logs: level WARNING containing Telegram’s error text.

#### 6. Other Telegram API errors (TelegramAPIError, generic)
	•	User message: “Telegram error. Please try again later.”
	•	Logs: level ERROR with the API error text.

#### 7. Unknown exceptions (Exception fallback)
	•	User message: “An unexpected error occurred. We’re already on it.”
	•	Logs: full traceback at level ERROR.
	•	Alert: traceback is sent to the developer chat.

#### 8. Graceful shutdown (asyncio.CancelledError)
	•	Action: middleware re-raises the exception so the event loop can shut down cleanly.
	•	Logs: not treated as an error.



Registration order
```python

dp.update.middleware.register(ServicesMiddleware())            # business DI
dp.update.middleware.register(ErrorHandlingMiddleware())       # last
```

---

### CI / CD guide — GitHub Actions → SSH deploy

Below are the steps you need to follow in order to ship every push to main straight to your VPS.

#### 1 · Prepare the server

#### On the VPS
```bash
sudo adduser engbot --disabled-password
sudo usermod -aG docker engbot
sudo mkdir -p /srv/engflowbot
sudo chown engbot:engbot /srv/engflowbot
```
- Generate an SSH key pair on your workstation (or in GH Secrets UI) and put the public half in ~engbot/.ssh/authorized_keys.



#### 2 · Create repository secrets

- SSH_PRIVATE_KEY	– Private part of the deploy key (multi-line, keep -----BEGIN …-----).
- SERVER_IP – Public IP or DNS of the VPS.
- SSH_USER – The Linux user that owns /srv/engflowbot (e.g. engbot).


#### 3 · Push & watch
	1.	git add . && git commit -m "feat: add super cool feature"
	2.	git push origin main
	3.	GitHub → Actions tab → Deploy job should turn green.
The bot restarts on your VPS automatically.

That’s it—full zero-downtime CI/CD with less than 50 lines of YAML.

---

### Road-map

	•	Native inline audio (replace Youglish)
	•	Prometheus + Grafana dashboard
	•	Mini-webapp (TWA) for content editing
