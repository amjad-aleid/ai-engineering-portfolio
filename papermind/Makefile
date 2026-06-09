.PHONY: install dev prod dev-all prod-all frontend ingest eval kill

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

# --- Kill any running API or frontend processes ---
kill:
	@pkill -f "uvicorn api.main:app" 2>/dev/null && echo "Stopped uvicorn" || true
	@pkill -f "streamlit run frontend/app.py" 2>/dev/null && echo "Stopped streamlit" || true

# --- Development ---
dev: kill
	APP_ENV=development .venv/bin/uvicorn api.main:app \
		--host 127.0.0.1 --port 8000 --reload

# --- Production ---
prod: kill
	APP_ENV=production .venv/bin/uvicorn api.main:app \
		--host 0.0.0.0 --port 8000 --workers 4

# --- Frontend (works in both envs) ---
frontend: kill
	APP_ENV=$(or $(APP_ENV),development) .venv/bin/streamlit run frontend/app.py

# --- Start API + frontend together (Ctrl+C stops both) ---
dev-all: kill
	@trap 'kill $$(jobs -p)' EXIT; \
	APP_ENV=development .venv/bin/uvicorn api.main:app \
		--host 127.0.0.1 --port 8000 --reload & \
	APP_ENV=development .venv/bin/streamlit run frontend/app.py

prod-all: kill
	@trap 'kill $$(jobs -p)' EXIT; \
	APP_ENV=production .venv/bin/uvicorn api.main:app \
		--host 0.0.0.0 --port 8000 --workers 4 & \
	APP_ENV=production .venv/bin/streamlit run frontend/app.py

# --- Ingest PDFs (pass files via ARGS) ---
# Usage: make ingest ARGS="paper.pdf paper2.pdf" APP_ENV=production
ingest:
	APP_ENV=$(or $(APP_ENV),development) .venv/bin/python ingest.py $(ARGS)

# --- Evaluation harness ---
# Usage: make eval ARGS="my_paper_id" APP_ENV=production
eval:
	APP_ENV=$(or $(APP_ENV),development) .venv/bin/python eval/evaluate.py $(ARGS)
