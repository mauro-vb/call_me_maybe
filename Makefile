PYTHON_VERSION	= 3.13.1
PYTHON			= python3
SRC				= src

all: run

check-uv:
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "uv is not installed. Please go to https://docs.astral.sh/uv/getting-started/installation/."; \
		exit 1; \
	fi

run: check-uv
	@uv run $(PYTHON) -m $(SRC)

debug: check-uv
	uv run $(PYTHON) -m pdb -m $(SRC)

install: check-uv
	@uv python install $(PYTHON_VERSION)
	@uv python pin $(PYTHON_VERSION)
	@uv sync

lint:
	@uv run python -m flake8 $(SRC)
	@mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs\
		--exclude 'llm_sdk'

lint-strict:
	@echo "\n-- Running flake8 --\n"
	-@$(VENV_PYTHON) -m flake8 $(SRC)
	@echo "Running mypy"
	-@$(VENV_PYTHON) -m mypy . --strict \
        --exclude '(build|dist|\.venv)'\
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

fix-lint: check-uv
	@uv run ruff check --fix

fix-format: check-uv
	@uv run ruff format

clean:
	@rm -rf .mypy_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: all install run debug lint lint-strict clean fix-lint fix-format
