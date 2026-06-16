DC = docker compose -f compose.yaml
RUN = $(DC) run --rm app
RUN_IT = $(DC) run --rm -it app

PACKAGES := shared due-date
TARGETS := $(if $(pkg),$(pkg),$(PACKAGES))
LINT_TARGETS := $(if $(pkg),$(pkg),$(PACKAGES) tests)
TEST_TARGETS := $(if $(pkg),$(pkg)/tests,tests $(addsuffix /tests,$(PACKAGES)))
SYNC = uv sync --frozen --inexact --all-groups $(if $(pkg),--package mpt-extension-contrib-$(pkg),--all-packages)

bash:  ## Open a bash shell in the dev image
	$(RUN_IT) bash

build:  ## Build the dev image
	$(DC) build

down:  ## Stop and remove containers
	$(DC) down

format:  ## Format code (ruff import-sort + format); pkg=<module> to scope
	$(RUN) bash -c "ruff check --select I --fix $(LINT_TARGETS) && ruff format $(LINT_TARGETS)"

check:  ## Run static checks: ruff, flake8, mypy, uv lock; pkg=<module> to scope
	$(RUN) bash -c "$(SYNC) && ruff format --check $(LINT_TARGETS) && ruff check $(LINT_TARGETS) && flake8 $(LINT_TARGETS) && mypy $(TARGETS) && uv lock --check"

test:  ## Run the test suite; pkg=<module> to scope
	$(RUN) bash -c "$(SYNC) && pytest $(TEST_TARGETS)"

check-all: check test  ## Run the full local validation flow (checks + tests)
