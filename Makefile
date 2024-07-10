.PHONY: dev format

dev:
ifeq ($(VIRTUAL_ENV),)
	poetry shell
else
	textual run --dev application.main:UI
endif

format: 
	ruff format && ruff check
