PYTHON=python3

.PHONY: all clean install format lint test dist

all: install test

# Install locally in editable mode with dev dependencies
install:
	$(PYTHON) -m pip install -e .[dev]

# Format code using black
format:
	black src tests

# Lint code using flake8
lint:
	flake8 src tests

# Run tests
test:
	$(PYTHON) -m unittest discover tests

# Build distribution (Wheel and Source)
dist: clean
	$(PYTHON) -m pip install build
	$(PYTHON) -m build

clean:
	rm -rf output/*.json
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf src/ips_sampler/__pycache__
	rm -rf tests/__pycache__
