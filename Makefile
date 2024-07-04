.PHONY: all format check

SRC = .
BLACK = black
ISORT = isort
AUTOFLAKE = autoflake
PYTHON_FILES = $(shell find $(SRC) -name "*.py")

dev:
	poetry shell && textual run --dev application.main:UI

format: 
	ruff format && ruff check

