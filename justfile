# --------------------
# justfile
# --------------------
set shell := ["bash", "-eu", "-o", "pipefail", "-c"]
set dotenv-load := false

# Help, the list of available commands
help:
    @just --list

# --------------------
# Audit & Security
# --------------------
# Audit the SCA and SAST
audit: sast
    @echo "Audit completed"

# Audit common security issues
sast:
    uv tool run bandit --configfile pyproject.toml --quiet --recursive .

# --------------------
# Formatting & Linting
# --------------------
# Fix Python code formatting, linting and sorting imports
fix:  
	uv tool run ruff format .
	uv tool run ruff check --fix .

# --------------------
# Install dependencies
# --------------------
# Install development dependencies
install-dev:
	uv pip install -r requirements/dev.txt
