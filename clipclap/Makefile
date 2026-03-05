.PHONY: setup setup-backend setup-frontend samples dev dev-backend dev-frontend clean

# Default target
all: setup samples

# Full setup
setup: setup-backend setup-frontend

# Python command (override with: make setup-backend PYTHON=python3.11)
PYTHON ?= python3

# Backend setup
setup-backend:
	@echo "Setting up Python backend..."
	cd backend && $(PYTHON) -m venv venv
	cd backend && ./venv/bin/pip install --upgrade pip setuptools wheel
	cd backend && ./venv/bin/pip install -r requirements.txt
	@echo "Backend setup complete!"

# Frontend setup
setup-frontend:
	@echo "Setting up Svelte frontend..."
	cd frontend && npm install
	@echo "Frontend setup complete!"

# Download sample data
samples:
	@echo "Downloading sample data..."
	cd backend && ./venv/bin/python download_samples.py

# Run both servers (requires two terminals or use 'make dev-backend' and 'make dev-frontend' separately)
dev:
	@echo "Starting development servers..."
	@echo "Run 'make dev-backend' in one terminal and 'make dev-frontend' in another"
	@echo "Or use: make dev-all (requires GNU parallel or similar)"

# Run backend only
dev-backend:
	@echo "Starting FastAPI backend on http://localhost:8000"
	cd backend && ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend only
dev-frontend:
	@echo "Starting Svelte frontend on http://localhost:5173"
	cd frontend && npm run dev

# Run both servers in background (for demo)
dev-all:
	@echo "Starting both servers..."
	cd backend && ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev &
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"

# Build frontend for production
build:
	cd frontend && npm run build

# Clean up
clean:
	rm -rf backend/venv
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf backend/app/**/__pycache__
	rm -rf frontend/node_modules
	rm -rf frontend/dist

# Help
help:
	@echo "CLIP & CLAP Edge Inference Demo - Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup          - Install all dependencies (backend + frontend)"
	@echo "  make setup-backend  - Install Python dependencies only"
	@echo "  make setup-frontend - Install npm dependencies only"
	@echo "  make samples        - Download sample images and audio"
	@echo "  make dev-backend    - Run FastAPI backend (port 8000)"
	@echo "  make dev-frontend   - Run Svelte frontend (port 5173)"
	@echo "  make build          - Build frontend for production"
	@echo "  make clean          - Remove all generated files"
