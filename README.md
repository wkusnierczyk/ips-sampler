# IPS Sampler

IPS Sampler is a repository with references to International Patient Summary sample collections as well as tools for generating synthetic mock samples.

## Contents

* [What is IPS](#what-is-ips)
* [Sample collections](#sample-collections)
* [Generator Tool (`ips-generator`)](#generator-tool-ips-generator)
* [Development & Makefile Targets](#development--makefile-targets)
* [About](#about)

---

## 

## What is IPS

The International Patient Summary (IPS) is a standardized, minimal, and non-exhaustive electronic health record extract designed for cross-border or unplanned care. 
It provides essential, specialty-agnostic patient information—mainly medications, allergies, and problems—to ensure safe, continuity of care across different health systems. 

### Key Components and Purpose

* **Core Data** Includes patient identification, medications, allergies, and a problem list as required elements.
* **Optional Data** May include immunizations, procedures, medical devices, and diagnostic results.
* **Standards** Built on ISO/EN 17269 and implemented using HL7 FHIR or CDA, often incorporating SNOMED CT.
* **Goal** To enable clinicians to access crucial, actionable data during emergencies or when a patient travels, regardless of location. 

### Usage and Implementation

* **Use Case** Primary focus is on unplanned, emergency care, but useful for routine care transitions.
* **Global Adoption**:  
  Supported by initiatives like the Global Digital Health Partnership (GDHP) involving 30 countries and the WHO.
* **Technology** Often integrated into Electronic Health Record (EHR) systems to facilitate data exchange, for example, through FHIR servers. 

### References

* [International Patient Summary Implementation Guide 2.0.0](https://build.fhir.org/ig/HL7/fhir-ips/en/)
* [The International Patient Summary](https://international-patient-summary.net/)
* [The International Patient Summary Terminology](https://www.snomed.org/international-patient-summary-terminology)
* [ISO 27269:2025 Health informatics — International patient summary](https://www.iso.org/standard/84639.html)

## Sample collections

* [**IPSViewer samples**](https://github.com/jddamore/IPSviewer/tree/main/samples)  
  GitHub: [github.com/jddamore/IPSviewer](https://github.com/jddamore/IPSviewer)
* [**Synthea Synthetic Patient Generation**](https://synthetichealth.github.io/synthea)  
  GitHub: [github.com/synthetichealth/synthea](https://github.com/synthetichealth/synthea)

---

## Generator Tool (`ips-generator`)

Included in this repository is `ips-generator`, a CLI tool and Python library for generating synthetic International Patient Summary (IPS) FHIR records.

### Features

* **Separation of Concerns:** Logic is contained in the `ips_generator` package.
* **Configurable:** Clinical data (conditions, medications) is loaded from `config/ips_config.json`.
* **Reproducible:** Supports deterministic generation via the `--seed` flag.
* **Standards Compliant:** Generates FHIR R4 Bundles (document type) suitable for IPS testing.
* **PDF Rendering:** Option to generate human-readable PDF documents alongside the JSON data.
* **Longitudinal Data Simulation:** Supports generating multiple distinct records for the same patient identity to test reconciliation and history tracking.

### Installation

To install the tool and its development dependencies locally:

```bash
make install
```

This installs the package in "editable" mode, meaning changes to the source code are immediately reflected in the installed command.

```bash
pip install .
```

This installs the package systemwide.


### Usage

#### Command Line Interface (CLI)

Once installed, use the `ips-generator` command:

```bash
# Generate records for 50 unique patients (default 1 record per patient)
ips-generator --patients 50

# Generate 3 distinct records for each of 10 patients (30 files total)
# Useful for testing reconciliation of conflicting/evolving data
ips-generator --patients 10 --repeats 3

# Generate 10 records with PDF counterparts
ips-generator --patients 10 --pdf

# Generate records to a specific folder with a seed (reproducible)
ips-generator -p 10 --output-dir ./my_data --seed 12345

# Generate minified JSON (no indentation)
ips-generator -p 100 --minify

# View tool information
ips-generator --about
```

#### Python Library

You can also use the generator programmatically in your own Python scripts:

```python
from ips_generator.generator import IPSGenerator

# Initialize with the path to your config file
gen = IPSGenerator("config/ips_config.json")

# Generate a batch of bundles
# Returns a tuple: (bundle, patient_index, record_index)
for bundle, p_idx, r_idx in gen.generate_batch(patient_count=5, repeats=2):
    print(f"Patient {p_idx} - Record {r_idx}: {bundle['id']}")
```

---

## Development & Makefile Targets

This project uses a `Makefile` to automate common development tasks.

| Target | Command | Description |
| :--- | :--- | :--- |
| **`install`** | `make install` | Installs the package in editable mode (`pip install -e .[dev]`) with all development dependencies (black, flake8, mypy, pytest, reportlab). |
| **`format`** | `make format` | formats the code automatically using **Black**. |
| **`lint`** | `make lint` | Checks code style and logical errors using **Flake8**. |
| **`type-check`** | `make type-check` | Performs static type analysis using **Mypy**. |
| **`test`** | `make test` | Runs the unit test suite using Python's `unittest` module. |
| **`dist`** | `make dist` | Builds distribution artifacts (Source Archive and Wheel) in the `dist/` directory. |
| **`clean`** | `make clean` | Removes build artifacts, cached files (`__pycache__`), output data, and temporary directories. |
| **`all`** | `make all` | Runs `install`, `type-check`, and `test` in sequence. |

### Running Tests

To ensure the generator is working correctly:

```bash
make test
```

## About

```bash
$ ips-generator --about

ips-generator: Synthetic International Patient Summary (IPS) Generator
├─ version:   0.1.2
├─ developer: mailto:waclaw.kusnierczyk@gmail.com
├─ source:    https://github.com/wkusnierczyk/ips-sampler
└─ licence:   MIT https://opensource.org/licenses/MIT
```
