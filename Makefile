.DEFAULT: help

help:
	@echo "make help"
	@echo "    display this help statement"
	@echo "make test"
	@echo "    run associated test suite with pytest"
	@echo "make lint"
	@echo "    lint project files using the flake8 linter"

test:
	pytest -W ignore::FutureWarning

lint:
	flake8 --exclude *env