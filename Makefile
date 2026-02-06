.PHONY: setup backend frontend dev

setup:
	@echo "Setting up backend..."
	cd backend && uv venv venv --python 3.12
	cd backend && . venv/bin/activate && uv pip install -r requirements.txt
	@echo "Setting up frontend..."
	cd frontend && npm install

backend:
	@echo "Starting backend..."
	. backend/venv/bin/activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Starting frontend..."
	cd frontend && npm run dev

dev:
	@echo "Starting both backend and frontend..."
	@echo "Use 'make -j2 backend frontend' to run in parallel, or run in separate terminals."
	$(MAKE) -j2 backend frontend
