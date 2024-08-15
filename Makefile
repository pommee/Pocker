.PHONY: dev format format-fix

dev:
ifeq ($(VIRTUAL_ENV),)
	poetry shell
else
	textual run --dev application.main:UI
endif

format: 
	ruff format --quiet && ruff check --quiet

format-fix: 
	ruff format && ruff check --fix 
