# Makefile for GIMP AI Integration

# Python interpreter
PYTHON := python

# Directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend
SCRIPTS_DIR := scripts
DOCS_DIR := docs

# Commands
PYTEST := pytest
BLACK := black
ISORT := isort
FLAKE8 := flake8
PIP := pip

.PHONY: help
help:
	@echo "GIMP AI Integration Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  help            - Show this help message"
	@echo "  install         - Install dependencies"
	@echo "  check-env       - Check environment"
	@echo "  deploy          - Deploy the plugin to GIMP"
	@echo "  test            - Run all tests"
	@echo "  test-backend    - Run backend tests"
	@echo "  test-integration - Run integration tests"
	@echo "  format          - Format code with Black and isort"
	@echo "  lint            - Check code style with flake8"
	@echo "  clean           - Remove build artifacts"
	@echo "  build           - Build distribution packages"
	@echo "  docs            - Build documentation"
	@echo "  serve           - Run the MCP server"

.PHONY: install
install:
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt
	$(PIP) install -r $(FRONTEND_DIR)/requirements.txt
	$(PIP) install -e .

.PHONY: check-env
check-env:
	$(PYTHON) $(SCRIPTS_DIR)/check_environment.py

.PHONY: deploy
deploy:
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py

.PHONY: test
test: test-backend test-integration

.PHONY: test-backend
test-backend:
	$(PYTEST) $(BACKEND_DIR)/tests

.PHONY: test-integration
test-integration:
	$(PYTHON) $(SCRIPTS_DIR)/integration_test.py

.PHONY: format
format:
	$(BLACK) $(BACKEND_DIR) $(FRONTEND_DIR) $(SCRIPTS_DIR)
	$(ISORT) $(BACKEND_DIR) $(FRONTEND_DIR) $(SCRIPTS_DIR)

.PHONY: lint
lint:
	$(FLAKE8) $(BACKEND_DIR) $(FRONTEND_DIR) $(SCRIPTS_DIR)

.PHONY: clean
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".pytest_cache" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "htmlcov" -exec rm -rf {} +

.PHONY: build
build:
	$(PYTHON) $(SCRIPTS_DIR)/build_distribution.py --all

.PHONY: docs
docs:
	@echo "Building documentation..."
	# Add documentation build commands if needed
	# For simple markdown docs, we can just copy them to a build directory
	mkdir -p build/docs
	cp $(DOCS_DIR)/*.md build/docs/

.PHONY: serve
serve:
	@echo "Starting MCP server..."
	$(PYTHON) $(BACKEND_DIR)/server/app.py
