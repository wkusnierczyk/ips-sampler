import uuid
from datetime import datetime, timedelta
import random

class IPSBuilder:
    """
    Fluent API Builder for a single IPS FHIR Bundle.
    """
    def __init__(self, data_config, seed=None):
        self.config = data_config
        self.rng = random.Random(seed) if seed is not None else random.Random()
        
        # Internal state
        self.patient_id = str(uuid.uuid4())
        self.practitioner_id = str(uuid.uuid4())
        self.resources = []
        self.sections = []
        self._init_core_resources()

    def _init_core_resources(self):
        # Create Patient
        fam = self.rng.choice(self.config["demographics"]["family_names"])
        giv = self.rng.choice(self.config["demographics"]["given_names"])
        
        patient = {
            "resourceType": "Patient",
            "id": self.patient_id,
            "active": True,
            "name": [{"family": fam, "given": [giv]}],
            "gender": self.rng.choice(["male", "female", "other", "unknown"]),
            "birthDate": (datetime.now() - timedelta(days=self.rng.randint(7000, 30000))).strftime("%Y-%m-%d")
        }
        
        # Create Practitioner (Author)
        practitioner = {
            "resourceType": "Practitioner",
            "id": self.practitioner_id,
            "name": [{"family": "Doctor", "given": ["Family"]}]
        }
        
        self.resources.extend([patient, practitioner])
        return self

    def add_condition(self):
        """Adds a random condition from config."""
        cond_def = self.rng.choice(self.config["clinical_data"]["conditions"])
        res_id = str(uuid.uuid4())
        
        condition = {
            "resourceType": "Condition",
            "id": res_id,
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "code": {"coding": [{"system": cond_def["system"], "code": cond_def["code"], "display": cond_def["display"]}]},
            "subject": {"reference": f"Patient/{self.patient_id}"}
        }
        
        self.resources.append(condition)
        self._ensure_section(
            "Problem List", 
            self.config["terminologies"]["loinc"]["problems"], 
            f"Condition/{res_id}"
        )
        return self

    def add_medication(self):
        """Adds a random medication from config."""
        med_def = self.rng.choice(self.config["clinical_data"]["medications"])
        res_id = str(uuid.uuid4())
        
        med_stmt = {
            "resourceType": "MedicationStatement",
            "id": res_id,
            "status": "active",
            "medicationCodeableConcept": {"coding": [{"system": med_def["system"], "code": med_def["code"], "display": med_def["display"]}]},
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "effectiveDateTime": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.resources.append(med_stmt)
        self._ensure_section(
            "Medication Summary", 
            self.config["terminologies"]["loinc"]["medications"], 
            f"MedicationStatement/{res_id}"
        )
        return self

    def add_allergy(self):
        """Adds a random allergy from config."""
        alg_def = self.rng.choice(self.config["clinical_data"]["allergies"])
        res_id = str(uuid.uuid4())
        
        allergy = {
            "resourceType": "AllergyIntolerance",
            "id": res_id,
            "code": {"coding": [{"system": alg_def["system"], "code": alg_def["code"], "display": alg_def["display"]}]},
            "patient": {"reference": f"Patient/{self.patient_id}"}
        }
        
        self.resources.append(allergy)
        self._ensure_section(
            "Allergies", 
            self.config["terminologies"]["loinc"]["allergies"], 
            f"AllergyIntolerance/{res_id}"
        )
        return self

    def _ensure_section(self, title, code, reference):
        """Helper to add references to the correct Composition section."""
        for sec in self.sections:
            if sec["code"]["coding"][0]["code"] == code:
                sec["entry"].append({"reference": reference})
                return
        
        # Section doesn't exist, create it
        new_section = {
            "title": title,
            "code": {"coding": [{"system": "http://loinc.org", "code": code}]},
            "entry": [{"reference": reference}]
        }
        self.sections.append(new_section)

    def build(self):
        """Assembles the final FHIR Bundle."""
        composition = {
            "resourceType": "Composition",
            "id": str(uuid.uuid4()),
            "status": "final",
            "type": {"coding": [{"system": "http://loinc.org", "code": self.config["terminologies"]["loinc"]["doc_type"]}]},
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "date": datetime.now().isoformat(),
            "author": [{"reference": f"Practitioner/{self.practitioner_id}"}],
            "title": "International Patient Summary",
            "section": self.sections
        }
        
        # Composition must be first in a Document Bundle
        all_entries = [{"resource": composition}] + [{"resource": r} for r in self.resources]
        
        return {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "type": "document",
            "timestamp": datetime.now().isoformat(),
            "entry": [{"fullUrl": f"urn:uuid:{e['resource']['id']}", "resource": e['resource']} for e in all_entries]
        }
