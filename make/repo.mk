## Repository-management targets. Do not modify shared *.mk files.

create-module:  ## Scaffold a new module from the copier template (module=<kebab-case-name>)
	$(call require,module)
	$(RUN) python scripts/scaffold_module.py --module $(module)
	@printf "\nScaffolded %s. Next: wire it into the workspace and run 'make build && make check-all pkg=%s'.\n" "$(module)" "$(module)"
