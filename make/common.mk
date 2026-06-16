DC = docker compose -f compose.yaml
RUN = $(DC) run --rm app
RUN_IT = $(DC) run --rm -it app

PACKAGES := shared due-date
TARGETS := $(if $(pkg),$(pkg),$(PACKAGES))
LINT_TARGETS := $(if $(pkg),$(pkg),$(PACKAGES) tests scripts)
TYPE_TARGETS := $(if $(pkg),$(pkg),$(PACKAGES) scripts)
TEST_TARGETS := $(if $(pkg),$(pkg)/tests,tests scripts/tests $(addsuffix /tests,$(PACKAGES)))
SYNC = uv sync --frozen --inexact --all-groups $(if $(pkg),--package mpt-extension-contrib-$(pkg),--all-packages)
UV_SYNC = uv sync --inexact --all-packages --all-groups
PKG_FLAG = $(if $(pkg),--package mpt-extension-contrib-$(pkg),)

bash:  ## Open a bash shell in the dev image
	$(RUN_IT) bash

build:  ## Build the dev image
	$(DC) build

down:  ## Stop and remove containers
	$(DC) down

format:  ## Format code (ruff import-sort + format); pkg=<module> to scope
	$(RUN) bash -c "ruff check --select I --fix $(LINT_TARGETS) && ruff format $(LINT_TARGETS)"

check: repo-check  ## Run repo structure check + ruff, flake8, mypy, uv lock; pkg=<module> to scope
	$(RUN) bash -c "$(SYNC) && ruff format --check $(LINT_TARGETS) && ruff check $(LINT_TARGETS) && flake8 $(LINT_TARGETS) && mypy $(TYPE_TARGETS) && uv lock --check"

test:  ## Run the test suite; pkg=<module> to scope
	$(RUN) bash -c "$(SYNC) && pytest $(TEST_TARGETS)"

check-all: check test  ## Run the full local validation flow (checks + tests)

uv-add:  ## Add a runtime dependency (dep=<dep>; pkg=<module> for one package, else workspace)
	$(call require,dep)
	$(RUN) uv add $(PKG_FLAG) $(dep)
	$(MAKE) build

uv-add-dev:  ## Add a dev dependency (dep=<dep>; pkg=<module> for one package, else workspace)
	$(call require,dep)
	$(RUN) uv add --dev $(PKG_FLAG) $(dep)
	$(MAKE) build

uv-upgrade:  ## Upgrade all deps, or one with dep=<package_name>, and refresh uv.lock
	$(RUN) bash -c "uv lock $(if $(dep),--upgrade-package $(dep),--upgrade) && $(UV_SYNC)"
	$(MAKE) build
