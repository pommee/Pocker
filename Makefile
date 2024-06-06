.PHONY: all format check

SRC = .
BLACK = black
ISORT = isort
AUTOFLAKE = autoflake
PYTHON_FILES = $(shell find $(SRC) -name "*.py")

dev:
	poetry shell && textual run --dev application.main:UI

format: format-black format-isort remove-unused-imports check

check: check-black check-isort

format-black:
	@echo "Formatting code with Black..."
	$(BLACK) $(SRC)

format-isort:
	@echo "Sorting imports with isort..."
	$(ISORT) $(SRC)

remove-unused-imports:
	@echo "Removing unused imports and variables with autoflake..."
	$(AUTOFLAKE) --in-place --remove-unused-variables --remove-all-unused-imports --recursive $(SRC)

check-black:
	@echo "Checking code formatting with Black..."
	$(BLACK) --check $(SRC)

check-isort:
	@echo "Checking import sorting with isort..."
	$(ISORT) --check $(SRC)
