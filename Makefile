.PHONY: setup backend frontend dev seed-data seed-data-agent

# Default values for seeding
TRAINERS ?= "Caroline Girvan" "Sydney Cummings"
LIMIT ?= 5
VIDEOS_PER_PLAYLIST ?= 3

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

seed-data:
	@echo "Seeding data for trainers: $(TRAINERS)"
	. backend/venv/bin/activate && python backend/scripts/seed_workouts_v2.py --trainers $(TRAINERS) --limit $(LIMIT)

seed-data-agent:
	@echo "Seeding data using ADK Agent curation for: $(TRAINERS)"
	. backend/venv/bin/activate && python backend/scripts/seed_workouts_v3.py --trainers $(TRAINERS) --videos_per_playlist $(VIDEOS_PER_PLAYLIST)

reset-db:
	@echo "Resetting workout_library collection..."
	. backend/venv/bin/activate && python backend/scripts/reset_db.py
