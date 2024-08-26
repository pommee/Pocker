.PHONY: dev format format-fix

dev:
	poetry run textual run --dev application.main:UI

format: 
	ruff format --quiet && ruff check --quiet

format-fix: 
	ruff format && ruff check --fix 
