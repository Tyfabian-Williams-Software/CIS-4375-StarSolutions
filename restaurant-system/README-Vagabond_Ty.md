# CIS-4375-StarSolutions
This is the current state of our project's repo

## Setup & Running

- Copy `.env.example` to `.env` and fill in `SECRET_KEY` and `DATABASE_URL` with your local credentials. Do not commit `.env`.
- Create a virtual environment and install dependencies: `pip install -r requirements.txt`.
- To run locally with sockets: `python run.py` (this uses Flask-SocketIO). If using `eventlet`, install it and the server will pick it up.

Security: remove any hard-coded credentials from source. The repository now contains `.env.example` and `.gitignore` to help with this.

## Production deployment (recommended)

This project uses Flask + Flask-SocketIO. For production we recommend:

- Use Python 3.11 (eventlet and some socket drivers are not yet stable on newer Python versions).
- Create a virtual environment and install pinned dependencies from `requirements.txt`.

Example steps (on a Linux host):

```bash
# create user and working directory, then clone repo to /opt/restaurant-system
cd /opt/restaurant-system
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Run with Gunicorn + eventlet (recommended if using Python 3.11):

```bash
# from project root
.venv/bin/gunicorn -c deploy/gunicorn_conf.py run:app
```

If you prefer gevent (useful when eventlet is incompatible with your Python version):

1. Install `gevent` (already included as an optional dependency in `requirements.txt`).
2. Edit `deploy/gunicorn_conf.py` and set `worker_class = 'gevent'`.
3. Start Gunicorn as above.

Systemd example: a unit file is provided at `deploy/restaurant.service`. Copy it to
`/etc/systemd/system/restaurant.service` and adjust `User`, `WorkingDirectory`, and `Environment.PATH`.

Notes and troubleshooting
- If the server falls back to the `threading` async driver it will still run but may not scale for many
	concurrent websocket connections. Check your logs for the `SocketIO async_mode selected: ...` message
	at startup to confirm which driver was chosen.
- If you need support for Python 3.13+, prefer `gevent` or run in an ASGI-based stack; eventlet
	historically lags newest CPython releases.

## Docker deployment (managed DB)

This section covers running the app in Docker while using a managed database (no local DB in compose).

Prerequisites

- Have a managed database endpoint available and the connection URL in SQLAlchemy format (for example:
	`mysql+pymysql://user:password@host:3306/dbname`).
- Copy `.env.example` to `.env` and fill in `SECRET_KEY` and `DATABASE_URL` (do NOT commit `.env`).

Step-by-step (deploy with docker-compose)

1. Build the Docker image:

```bash
docker build -t restaurant-system:latest .
```

2. Start the container with your `.env` file (ensure `.env` contains `DATABASE_URL` for the managed DB):

```bash
docker-compose --env-file .env up -d --build
```

3. Verify the app is reachable on the exposed port (default 8000):

```bash
curl -I http://localhost:8000
```

Notes on secrets

- Keep `.env` out of version control. Use Docker secrets or your orchestration platform's secret store in
	production (Docker Swarm, Kubernetes, ECS secrets, etc.).

Gevent vs Eventlet — will they interfere?

- They are separate async libraries. Choosing `gevent` in the container (via `WORKER_CLASS=gevent`) does not
	"interfere" with `eventlet` as long as the image/command uses the desired worker library. Problems arise when
	the runtime tries to import an incompatible driver (for example, eventlet on Python 3.13) — that's why the
	image and environment must be consistent.
- The Dockerfile now respects the `WORKER_CLASS` env var at container start, so you can build a single image and
	select `eventlet` (recommended on Python 3.11) or `gevent` (recommended if you need Python 3.13) at runtime.

Examples

- To run with gevent workers (for Python 3.13 hosts or when eventlet is incompatible):

```bash
export WORKER_CLASS=gevent
export GUNICORN_WORKERS=3
docker-compose --env-file .env up -d --build
```

- To run with eventlet workers (recommended on Python 3.11):

```bash
export WORKER_CLASS=eventlet
export GUNICORN_WORKERS=2
docker-compose --env-file .env up -d --build
```

If you want, I can add a small `wait-for-db.sh` script to the image so the app waits for the managed DB to be reachable before starting. This is optional for managed DBs that are always available. 
