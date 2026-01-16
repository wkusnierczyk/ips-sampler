PYTHON=python3

.PHONY: all clean install format lint test dist

all: install test

install:
	$(PYTHON) -m pip install -e .[dev]

format:
	black src tests

lint:
	flake8 src tests

# PYTHONPATH=src ensures tests run even if package isn't installed in env
test:
	PYTHONPATH=src $(PYTHON) -m unittest discover tests

dist: clean
	$(PYTHON) -m pip install build
	$(PYTHON) -m build

clean:
	rm -rf output/*.json
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf src/ips_generator/__pycache__
	rm -rf tests/__pycache__
