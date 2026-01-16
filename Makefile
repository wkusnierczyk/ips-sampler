PYTHON=python3

.PHONY: all clean install format lint type-check test dist docs

all: install type-check test

install:
	$(PYTHON) -m pip install -e .[dev]
	$(PYTHON) -m pip install -r requirements.txt

format:
	black src tests

lint:
	flake8 src tests

# Static type checking
type-check:
	mypy src

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover tests

# Generate HTML documentation
docs:
	pdoc -o docs src/ips_generator

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
	rm -rf .mypy_cache
