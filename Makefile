.PHONY: run dev build seed test backend frontend clean help

PYTHON = /Users/kunalkakde/project antigravity/.venv/bin/python
UVICORN = /Users/kunalkakde/project antigravity/.venv/bin/uvicorn
ALEMBIC = /Users/kunalkakde/project antigravity/.venv/bin/alembic

help:
	@echo "AuditFlow AI — Available Commands:"
	@echo "  make run      - Run backend (port 8000) and frontend (port 3000) concurrently"
	@echo "  make backend  - Run FastAPI backend on port 8000"
	@echo "  make frontend - Run Next.js frontend on port 3000"
	@echo "  make seed     - Seed demo database with enterprise organizations and shipments"
	@echo "  make build    - Build Next.js frontend production bundle"
	@echo "  make clean    - Remove sqlite DB and caches"

seed:
	@echo "Seeding AuditFlow AI database..."
	@export PYTHONPATH="./backend" && $(PYTHON) -m app.seed

backend:
	@echo "Starting AuditFlow AI Backend API on http://localhost:8000 ..."
	@export PYTHONPATH="./backend" && $(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	@echo "Starting AuditFlow AI Next.js Frontend on http://localhost:3000 ..."
	@export PATH="$$HOME/.local/bin:$$PATH" && eval "$$(fnm env 2>/dev/null)" || true && cd frontend && npm run dev

build:
	@echo "Building frontend..."
	@export PATH="$$HOME/.local/bin:$$PATH" && eval "$$(fnm env 2>/dev/null)" || true && cd frontend && npm run build

run:
	@echo "Starting full AuditFlow AI Stack (Backend + Frontend)..."
	@make seed
	@(trap 'kill 0' SIGINT; \
		(export PYTHONPATH="./backend" && $(UVICORN) app.main:app --host 0.0.0.0 --port 8000) & \
		(export PATH="$$HOME/.local/bin:$$PATH" && eval "$$(fnm env 2>/dev/null)" || true && cd frontend && npm run dev) & \
		wait)

dev: run

clean:
	@rm -rf backend/auditflow.db auditflow.db frontend/.next data/storage
	@echo "Cleaned database and build caches."
