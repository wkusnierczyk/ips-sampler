"""
IPS Builder Module.

This module contains the IPSBuilder class, which implements a fluent API for
constructing individual International Patient Summary (IPS) FHIR Bundles.
It handles the creation of FHIR resources and the Composition resource that
binds them together.
"""

import uuid
from datetime import datetime, timedelta
import random
from typing import Any, Dict, List, Optional

# Type alias for clarity
FHIRResource = Dict[str, Any]


class IPSBuilder:
    """
    Fluent API Builder for a single IPS FHIR Bundle.

    This class manages the state of a single patient record being generated. It allows
    for step-by-step addition of clinical content (conditions, medications, allergies)
    and final assembly into a FHIR Document Bundle.

    Attributes:
        config (Dict[str, Any]): The configuration dictionary containing clinical data.
        rng (random.Random): Seeded random number generator.
        patient_id (str): UUID for the Patient resource.
        practitioner_id (str): UUID for the Practitioner resource.
        resources (List[FHIRResource]): List of FHIR resources created so far.
        sections (List[Dict[str, Any]]): List of sections for the Composition resource.
    """

    def __init__(self, data_config: Dict[str, Any], seed: Optional[int] = None):
        """
        Initialize the builder.

        Args:
            data_config (Dict[str, Any]): Configuration dictionary with data options.
            seed (Optional[int]): Random seed for this specific record generation.
        """
        self.config = data_config
        self.rng = random.Random(seed) if seed is not None else random.Random()

        # Internal state
        self.patient_id = self._generate_uuid()
        self.practitioner_id = self._generate_uuid()
        self.resources: List[FHIRResource] = []
        self.sections: List[Dict[str, Any]] = []
        self._init_core_resources()

    def _generate_uuid(self) -> str:
        """
        Generate a reproducible UUID based on the seeded RNG.

        Returns:
            str: A string representation of a UUID.
        """
        return str(uuid.UUID(int=self.rng.getrandbits(128)))

    def _init_core_resources(self) -> "IPSBuilder":
        """
        Initialize the core resources (Patient, Practitioner) for the bundle.

        Selects random demographics based on configuration and adds the resources
        to the internal list.

        Returns:
            IPSBuilder: Returns self for method chaining.
        """
        fam = self.rng.choice(self.config["demographics"]["family_names"])
        giv = self.rng.choice(self.config["demographics"]["given_names"])

        birth_days_ago = self.rng.randint(7000, 30000)
        birth_date = datetime.now() - timedelta(days=birth_days_ago)

        patient: FHIRResource = {
            "resourceType": "Patient",
            "id": self.patient_id,
            "active": True,
            "name": [{"family": fam, "given": [giv]}],
            "gender": self.rng.choice(["male", "female", "other", "unknown"]),
            "birthDate": birth_date.strftime("%Y-%m-%d"),
        }

        practitioner: FHIRResource = {
            "resourceType": "Practitioner",
            "id": self.practitioner_id,
            "name": [{"family": "Doctor", "given": ["Family"]}],
        }

        self.resources.extend([patient, practitioner])
        return self

    def add_condition(self) -> "IPSBuilder":
        """
        Add a random condition (problem) to the record.

        Selects a condition from the configuration, creates a Condition resource,
        and adds it to the 'Problem List' section.

        Returns:
            IPSBuilder: Returns self for method chaining.
        """
        cond_def = self.rng.choice(self.config["clinical_data"]["conditions"])
        res_id = self._generate_uuid()

        condition: FHIRResource = {
            "resourceType": "Condition",
            "id": res_id,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/"
                        "condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "code": {
                "coding": [
                    {
                        "system": cond_def["system"],
                        "code": cond_def["code"],
                        "display": cond_def["display"],
                    }
                ]
            },
            "subject": {"reference": f"Patient/{self.patient_id}"},
        }

        self.resources.append(condition)
        self._ensure_section(
            "Problem List",
            self.config["terminologies"]["loinc"]["problems"],
            f"Condition/{res_id}",
        )
        return self

    def add_medication(self) -> "IPSBuilder":
        """
        Add a random medication statement to the record.

        Selects a medication from the configuration, creates a MedicationStatement
        resource, and adds it to the 'Medication Summary' section.

        Returns:
            IPSBuilder: Returns self for method chaining.
        """
        med_def = self.rng.choice(self.config["clinical_data"]["medications"])
        res_id = self._generate_uuid()

        med_stmt: FHIRResource = {
            "resourceType": "MedicationStatement",
            "id": res_id,
            "status": "active",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": med_def["system"],
                        "code": med_def["code"],
                        "display": med_def["display"],
                    }
                ]
            },
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "effectiveDateTime": datetime.now().strftime("%Y-%m-%d"),
        }

        self.resources.append(med_stmt)
        self._ensure_section(
            "Medication Summary",
            self.config["terminologies"]["loinc"]["medications"],
            f"MedicationStatement/{res_id}",
        )
        return self

    def add_allergy(self) -> "IPSBuilder":
        """
        Add a random allergy intolerance to the record.

        Selects an allergy from the configuration, creates an AllergyIntolerance
        resource, and adds it to the 'Allergies' section.

        Returns:
            IPSBuilder: Returns self for method chaining.
        """
        alg_def = self.rng.choice(self.config["clinical_data"]["allergies"])
        res_id = self._generate_uuid()

        allergy: FHIRResource = {
            "resourceType": "AllergyIntolerance",
            "id": res_id,
            "code": {
                "coding": [
                    {
                        "system": alg_def["system"],
                        "code": alg_def["code"],
                        "display": alg_def["display"],
                    }
                ]
            },
            "patient": {"reference": f"Patient/{self.patient_id}"},
        }

        self.resources.append(allergy)
        self._ensure_section(
            "Allergies",
            self.config["terminologies"]["loinc"]["allergies"],
            f"AllergyIntolerance/{res_id}",
        )
        return self

    def _ensure_section(self, title: str, code: str, reference: str) -> None:
        """
        Ensure a section exists in the Composition and add a reference to it.

        If the section with the given code exists, the reference is appended.
        Otherwise, a new section is created.

        Args:
            title (str): Title of the section.
            code (str): LOINC code for the section.
            reference (str): Relative reference to the resource (e.g.,
            "Condition/uuid").
        """
        for sec in self.sections:
            if sec["code"]["coding"][0]["code"] == code:
                sec["entry"].append({"reference": reference})
                return

        new_section = {
            "title": title,
            "code": {"coding": [{"system": "http://loinc.org", "code": code}]},
            "entry": [{"reference": reference}],
        }
        self.sections.append(new_section)

    def build(self) -> FHIRResource:
        """
        Finalize and build the IPS FHIR Bundle.

        Creates the Composition resource linking all sections and resources,
        and wraps everything into a Bundle of type 'document'.

        Returns:
            FHIRResource: The complete FHIR Bundle as a dictionary.
        """
        loinc = self.config["terminologies"]["loinc"]
        composition: FHIRResource = {
            "resourceType": "Composition",
            "id": self._generate_uuid(),
            "status": "final",
            "type": {
                "coding": [{"system": "http://loinc.org", "code": loinc["doc_type"]}]
            },
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "date": datetime.now().isoformat(),
            "author": [{"reference": f"Practitioner/{self.practitioner_id}"}],
            "title": "International Patient Summary",
            "section": self.sections,
        }

        all_entries = [{"resource": composition}]
        all_entries += [{"resource": r} for r in self.resources]

        return {
            "resourceType": "Bundle",
            "id": self._generate_uuid(),
            "type": "document",
            "timestamp": datetime.now().isoformat(),
            "entry": [
                {
                    "fullUrl": f"urn:uuid:{e['resource']['id']}",
                    "resource": e["resource"],
                }
                for e in all_entries
            ],
        }
