all: format lint

FILES := setup.py jelapi tests

.PHONY: format
format:  # Fix some linting issues in the project
	black $(FILES)
	isort $(FILES)

.PHONY: lint
lint:  # Show linting issues in the project
	flake8 $(FILES)
