# ips-sampler

IPS Sampler is a repository with references to International Patient Summary sample collections as well as tools for generating synthetic mock samples.

## What is IPS

The International Patient Summary (IPS) is a standardized, minimal, and non-exhaustive electronic health record extract designed for cross-border or unplanned care. 
It provides essential, specialty-agnostic patient information—mainly medications, allergies, and problems—to ensure safe, continuity of care across different health systems. 

### Key Components and Purpose

* **Core Data**  
  Includes patient identification, medications, allergies, and a problem list as required elements.
* **Optional Data**  
  May include immunizations, procedures, medical devices, and diagnostic results.
* **Standards**  
  Built on ISO/EN 17269 and implemented using HL7 FHIR or CDA, often incorporating SNOMED CT.
* **Goal**  
  To enable clinicians to access crucial, actionable data during emergencies or when a patient travels, regardless of location. 

### Usage and Implementation

* **Use Case**  
  Primary focus is on unplanned, emergency care, but useful for routine care transitions.
* **Global Adoption**:  
  Supported by initiatives like the Global Digital Health Partnership (GDHP) involving 30 countries and the WHO.
* **Technology**  
  Often integrated into Electronic Health Record (EHR) systems to facilitate data exchange, for example, through FHIR servers. 

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

## Generator

A CLI tool and library for generating synthetic International Patient Summary (IPS) FHIR records.

### Features

* **Separation of Concerns:** Logic is in `src/ips_gen`, CLI is `src/cli.py`.
* **Configurable:** All clinical data is loaded from `config/ips_config.json`.
* **Reproducible:** Supports `--seed` for deterministic generation.

### Usage

**Command Line**

```bash
# Generate 50 records
python src/cli.py --samples 50

# Generate 10 records to a specific folder with a seed
python src/cli.py -s 10 -o ./my_data --seed 12345
```

**Library (Python)**

```python
from ips_gen.generator import IPSGenerator

gen = IPSGenerator("config/ips_config.json")
for bundle in gen.generate_batch(count=5):
    print(bundle['id'])
```

### Testing
Run the test suite:

```bash
make test
```
