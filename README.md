# Synthetic IPS (International Patient Summary) Data

This project generates synthetic FHIR R4 Bundles formatted as International Patient Summaries (IPS).

## Purpose
To provide a local, lightweight dataset for developing and testing IPS viewers or validation tools.

## Content
The generator produces a FHIR `Bundle` of type `document`. The first entry is always the `Composition` resource, followed by referenced resources:
* Patient
* Practitioner
* AllergyIntolerance
* MedicationStatement
* Condition (Problems)

## Usage

1.  **Generate Data**:
    ```bash
    make generate
    ```

2.  **Output**:
    JSON files are located in `data/`.

## Standards
These records attempt to follow the [HL7 FHIR IPS Implementation Guide](http://hl7.org/fhir/uv/ips/), but are simplified for development speed. For production validation, please cross-reference with official HL7 examples.
