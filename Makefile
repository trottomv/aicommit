.PHONY: fix
fix:  ## Fix Python code formatting, linting and sorting imports
	uv tool run ruff format .
	uv tool run ruff check --fix .