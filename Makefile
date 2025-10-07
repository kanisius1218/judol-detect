.PHONY: help install test run clean setup lint format

help:
	@echo "Multi-Platform Spam Moderator - Available Commands"
	@echo "=================================================="
	@echo "  make install    - Install dependencies"
	@echo "  make setup      - Setup project (first time)"
	@echo "  make test       - Run tests"
	@echo "  make run        - Run bot (interactive)"
	@echo "  make run-once   - Run bot once"
	@echo "  make schedule   - Run scheduled moderation"
	@echo "  make stats      - Show statistics"
	@echo "  make clean      - Clean generated files"
	@echo "  make lint       - Run linting"
	@echo "  make format     - Format code"
	@echo "=================================================="

install:
	pip install -r requirements.txt

setup:
	@echo "Setting up project..."
	pip install -r requirements.txt
	@if not exist .env copy .env.example .env
	@if not exist logs mkdir logs
	@if not exist reports mkdir reports
	@echo "Setup complete! Edit .env with your API keys."

test:
	python tests/test_all.py

run:
	python run.py

run-once:
	python run.py --once

schedule:
	python run.py --scheduled

stats:
	python run.py --stats --days 7

clean:
	@echo "Cleaning generated files..."
	@if exist __pycache__ rmdir /s /q __pycache__
	@if exist src\__pycache__ rmdir /s /q src\__pycache__
	@if exist tests\__pycache__ rmdir /s /q tests\__pycache__
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"
	@for /r . %%f in (*.pyo) do @if exist "%%f" del "%%f"
	@echo "Clean complete!"

lint:
	@echo "Running linting (install flake8 if needed)..."
	@python -m flake8 src/ tests/ --max-line-length=100 --ignore=E501,W503

format:
	@echo "Formatting code (install black if needed)..."
	@python -m black src/ tests/ --line-length=100
