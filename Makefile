# Makefile for IPS Generator

.PHONY: all generate clean

all: generate

generate:
	python3 generators/ips_generator.py

clean:
	rm -f data/*.json
	echo "Cleaned data directory"
