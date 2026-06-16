## Repository-management targets. Do not modify shared *.mk files.

create-module:  ## Scaffold a new module from the copier template (module=<kebab-case-name>)
	$(call require,module)
	$(RUN) python scripts/scaffold_module.py --module $(module)
	$(RUN) uv lock
	$(MAKE) build
	@printf "\nCreated and wired %s. Validate with: make check-all pkg=%s\n" "$(module)" "$(module)"
