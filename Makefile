all: format lint

.PHONY: format
format:  # Fix some linting issues in the project
	black jelapi
	isort jelapi

.PHONY: lint
lint:  # Show linting issues in the project
	flake8 jelapi
