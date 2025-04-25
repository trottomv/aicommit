.PHONY: fix
fix:  ## Fix Python code formatting, linting and sorting imports
	python3 -m ruff format .
	python3 -m ruff check --fix .