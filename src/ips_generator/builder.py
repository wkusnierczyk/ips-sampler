import uuid
from datetime import datetime, timedelta
import random
from typing import Any, Dict, List, Optional

# Type alias for clarity
FHIRResource = Dict[str, Any]


class IPSBuilder:
    """
    Fluent API Builder for a single IPS FHIR Bundle.
    Handles the creation of core and optional IPS sections.
    """

    def __init__(
        self,
        data_config: Dict[str, Any],
        seed: Optional[int] = None,
        patient_context: Optional[Dict[str, Any]] = None,
    ):
        self.config = data_config
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.patient_context = patient_context

        # Internal state
        self.patient_id = (
            patient_context["id"] if patient_context else self._generate_uuid()
        )
        # Practitioner is usually different per record/author, so we regen it
        self.practitioner_id = self._generate_uuid()

        self.resources: List[FHIRResource] = []
        self.sections: List[Dict[str, Any]] = []
        self._init_core_resources()

    def _generate_uuid(self) -> str:
        """Generates a reproducible UUID based on the seeded RNG."""
        return str(uuid.UUID(int=self.rng.getrandbits(128)))

    def _random_date(self, start_days_ago: int, end_days_ago: int) -> str:
        """Generates a random date string (YYYY-MM-DD)."""
        days = self.rng.randint(start_days_ago, end_days_ago)
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    def _init_core_resources(self) -> "IPSBuilder":
        # 1. Determine Patient Data (Reuse context if provided, else generate)
        if self.patient_context:
            pat_data = self.patient_context
        else:
            fam = self.rng.choice(self.config["demographics"]["family_names"])
            giv = self.rng.choice(self.config["demographics"]["given_names"])
            birth_date = self._random_date(7000, 30000)
            gender = self.rng.choice(["male", "female", "other", "unknown"])

            pat_data = {
                "id": self.patient_id,
                "family": fam,
                "given": giv,
                "birthDate": birth_date,
                "gender": gender,
            }

        # 2. Build Patient Resource
        patient: FHIRResource = {
            "resourceType": "Patient",
            "id": pat_data["id"],
            "active": True,
            "name": [{"family": pat_data["family"], "given": [pat_data["given"]]}],
            "gender": pat_data["gender"],
            "birthDate": pat_data["birthDate"],
        }

        # 3. Build Practitioner Resource
        practitioner: FHIRResource = {
            "resourceType": "Practitioner",
            "id": self.practitioner_id,
            "name": [{"family": "Doctor", "given": ["Family"]}],
        }

        self.resources.extend([patient, practitioner])
        return self

    # --- Core Sections ---

    def add_condition(self) -> "IPSBuilder":
        cond_def = self.rng.choice(self.config["clinical_data"]["conditions"])
        res_id = self._generate_uuid()
        onset_date = self._random_date(100, 3000)

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
            "onsetDateTime": onset_date,
        }

        self.resources.append(condition)
        self._ensure_section(
            "Problem List",
            self.config["terminologies"]["loinc"]["problems"],
            f"Condition/{res_id}",
        )
        return self

    def add_medication(self) -> "IPSBuilder":
        med_def = self.rng.choice(self.config["clinical_data"]["medications"])
        res_id = self._generate_uuid()
        effective_date = self._random_date(10, 365)

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
            "effectiveDateTime": effective_date,
        }

        self.resources.append(med_stmt)
        self._ensure_section(
            "Medication Summary",
            self.config["terminologies"]["loinc"]["medications"],
            f"MedicationStatement/{res_id}",
        )
        return self

    def add_allergy(self) -> "IPSBuilder":
        alg_def = self.rng.choice(self.config["clinical_data"]["allergies"])
        res_id = self._generate_uuid()

        allergy: FHIRResource = {
            "resourceType": "AllergyIntolerance",
            "id": res_id,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/"
                        "allergyintolerance-clinical",
                        "code": "active",
                    }
                ]
            },
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
            "recordedDate": self._random_date(100, 5000),
        }

        self.resources.append(allergy)
        self._ensure_section(
            "Allergies and Intolerances",
            self.config["terminologies"]["loinc"]["allergies"],
            f"AllergyIntolerance/{res_id}",
        )
        return self

    # --- Extended History Sections ---

    def add_immunization(self) -> "IPSBuilder":
        imm_def = self.rng.choice(self.config["clinical_data"]["immunizations"])
        res_id = self._generate_uuid()
        occ_date = self._random_date(30, 1000)

        immunization: FHIRResource = {
            "resourceType": "Immunization",
            "id": res_id,
            "status": "completed",
            "vaccineCode": {
                "coding": [
                    {
                        "system": imm_def["system"],
                        "code": imm_def["code"],
                        "display": imm_def["display"],
                    }
                ]
            },
            "patient": {"reference": f"Patient/{self.patient_id}"},
            "occurrenceDateTime": occ_date,
        }

        self.resources.append(immunization)
        self._ensure_section(
            "History of Immunizations",
            self.config["terminologies"]["loinc"]["immunizations"],
            f"Immunization/{res_id}",
        )
        return self

    def add_procedure(self) -> "IPSBuilder":
        proc_def = self.rng.choice(self.config["clinical_data"]["procedures"])
        res_id = self._generate_uuid()
        perf_date = self._random_date(200, 4000)

        procedure: FHIRResource = {
            "resourceType": "Procedure",
            "id": res_id,
            "status": "completed",
            "code": {
                "coding": [
                    {
                        "system": proc_def["system"],
                        "code": proc_def["code"],
                        "display": proc_def["display"],
                    }
                ]
            },
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "performedDateTime": perf_date,
        }

        self.resources.append(procedure)
        self._ensure_section(
            "History of Procedures",
            self.config["terminologies"]["loinc"]["procedures"],
            f"Procedure/{res_id}",
        )
        return self

    def add_medical_device(self) -> "IPSBuilder":
        dev_def = self.rng.choice(self.config["clinical_data"]["devices"])
        res_id = self._generate_uuid()

        device: FHIRResource = {
            "resourceType": "Device",
            "id": res_id,
            "type": {
                "coding": [
                    {
                        "system": dev_def["system"],
                        "code": dev_def["code"],
                        "display": dev_def["display"],
                    }
                ]
            },
            "patient": {"reference": f"Patient/{self.patient_id}"},
        }

        self.resources.append(device)
        self._ensure_section(
            "Medical Devices",
            self.config["terminologies"]["loinc"]["devices"],
            f"Device/{res_id}",
        )
        return self

    def add_lab_result(self) -> "IPSBuilder":
        lab_def = self.rng.choice(self.config["clinical_data"]["lab_results"])
        res_id = self._generate_uuid()
        eff_date = self._random_date(1, 60)

        observation: FHIRResource = {
            "resourceType": "Observation",
            "id": res_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/"
                            "observation-category",
                            "code": "laboratory",
                            "display": "Laboratory",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": lab_def["system"],
                        "code": lab_def["code"],
                        "display": lab_def["display"],
                    }
                ]
            },
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "effectiveDateTime": eff_date,
            "valueString": lab_def["value"],
        }

        self.resources.append(observation)
        self._ensure_section(
            "Diagnostic Results",
            self.config["terminologies"]["loinc"]["results"],
            f"Observation/{res_id}",
        )
        return self

    def _ensure_section(self, title: str, code: str, reference: str) -> None:
        for sec in self.sections:
            if sec["code"]["coding"][0]["code"] == code:
                sec["entry"].append({"reference": reference})
                return

        new_section = {
            "title": title,
            "code": {"coding": [{"system": "http://loinc.org", "code": code}]},
            "text": {
                "status": "generated",
                "div": f"<div xmlns='http://www.w3.org/1999/xhtml'>{title}</div>",
            },
            "entry": [{"reference": reference}],
        }
        self.sections.append(new_section)

    def build(self) -> FHIRResource:
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
