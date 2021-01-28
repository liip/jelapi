all: format lint

.PHONY: format
format:  # Fix some linting issues in the project
	black setup.py jelapi
	isort setup.py jelapi

.PHONY: lint
lint:  # Show linting issues in the project
	flake8 jelapi
