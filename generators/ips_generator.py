import json
import random
import uuid
from datetime import datetime, timedelta

# ---------------------------------------------------------
# CONSTANTS & TERMINOLOGY
# ---------------------------------------------------------

OUTPUT_DIR = "data"
RECORD_COUNT = 20

# LOINC Codes for Sections
LOINC_ALLERGIES = "48765-2"
LOINC_MEDICATIONS = "10160-0"
LOINC_PROBLEMS = "11450-4"

# SNOMED sample codes
CONDITIONS = [
    {"code": "38341003", "display": "Hypertension"},
    {"code": "73211009", "display": "Diabetes mellitus"},
    {"code": "195967001", "display": "Asthma"},
    {"code": "22298006", "display": "Myocardial infarction"}
]

MEDICATIONS = [
    {"code": "319864", "display": "Hydrochlorothiazide 25 MG", "system": "http://www.nlm.nih.gov/research/umls/rxnorm"},
    {"code": "197361", "display": "Amlodipine 5 MG", "system": "http://www.nlm.nih.gov/research/umls/rxnorm"},
    {"code": "860975", "display": "Metformin 500 MG", "system": "http://www.nlm.nih.gov/research/umls/rxnorm"}
]

ALLERGENS = [
    {"code": "91936005", "display": "Penicillin allergy"},
    {"code": "300916003", "display": "Latex allergy"},
    {"code": "293637006", "display": "Peanut allergy"}
]

# ---------------------------------------------------------
# FHIR RESOURCE BUILDERS
# ---------------------------------------------------------

def create_patient_resource(patient_id):
    genders = ["male", "female", "other", "unknown"]
    family_names = ["Smith", "Garcia", "Kim", "Muller", "Rossi", "Ivanov"]
    given_names = ["James", "Maria", "Wei", "Anna", "Luca", "Olga"]
    
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "identifier": [
            {
                "system": "urn:oid:2.16.840.1.113883.2.4.6.3",
                "value": str(random.randint(100000000, 999999999))
            }
        ],
        "active": True,
        "name": [
            {
                "family": random.choice(family_names),
                "given": [random.choice(given_names)]
            }
        ],
        "gender": random.choice(genders),
        "birthDate": (datetime.now() - timedelta(days=random.randint(7000, 30000))).strftime("%Y-%m-%d")
    }

def create_condition_resource(patient_id, condition_def):
    res_id = str(uuid.uuid4())
    return {
        "resourceType": "Condition",
        "id": res_id,
        "clinicalStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
        },
        "verificationStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
        },
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": condition_def["code"],
                    "display": condition_def["display"]
                }
            ]
        },
        "subject": {"reference": f"Patient/{patient_id}"}
    }, res_id

def create_medication_statement(patient_id, med_def):
    res_id = str(uuid.uuid4())
    return {
        "resourceType": "MedicationStatement",
        "id": res_id,
        "status": "active",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": med_def["system"],
                    "code": med_def["code"],
                    "display": med_def["display"]
                }
            ]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": datetime.now().strftime("%Y-%m-%d")
    }, res_id

def create_allergy_intolerance(patient_id, allergy_def):
    res_id = str(uuid.uuid4())
    return {
        "resourceType": "AllergyIntolerance",
        "id": res_id,
        "clinicalStatus": {
             "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]
        },
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": allergy_def["code"],
                    "display": allergy_def["display"]
                }
            ]
        },
        "patient": {"reference": f"Patient/{patient_id}"}
    }, res_id

def create_composition(patient_id, author_id, sections):
    # This is the 'Header' of the IPS document
    return {
        "resourceType": "Composition",
        "id": str(uuid.uuid4()),
        "status": "final",
        "type": {
            "coding": [
                {"system": "http://loinc.org", "code": "60591-5", "display": "Patient Summary Document"}
            ]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "date": datetime.now().isoformat(),
        "author": [{"reference": f"Practitioner/{author_id}"}],
        "title": "International Patient Summary",
        "section": sections
    }

def generate_ips_bundle(index):
    bundle_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())
    practitioner_id = str(uuid.uuid4())
    
    # 1. Create Core Resources
    patient = create_patient_resource(patient_id)
    practitioner = {
        "resourceType": "Practitioner",
        "id": practitioner_id,
        "name": [{"family": "Doctor", "given": ["Family"]}]
    }

    entries = []
    
    # 2. Generate Clinical Data
    # Problems
    problem_refs = []
    problems_entry = []
    if random.choice([True, False]): # 50% chance of having problems
        for cond in random.sample(CONDITIONS, k=random.randint(1, 2)):
            res, rid = create_condition_resource(patient_id, cond)
            problems_entry.append({"resource": res})
            problem_refs.append({"reference": f"Condition/{rid}"})

    # Medications
    med_refs = []
    meds_entry = []
    if random.choice([True, False]):
        for med in random.sample(MEDICATIONS, k=random.randint(1, 2)):
            res, rid = create_medication_statement(patient_id, med)
            meds_entry.append({"resource": res})
            med_refs.append({"reference": f"MedicationStatement/{rid}"})

    # Allergies
    alg_refs = []
    algs_entry = []
    if random.choice([True, False]):
        for alg in random.sample(ALLERGENS, k=random.randint(1, 1)):
            res, rid = create_allergy_intolerance(patient_id, alg)
            algs_entry.append({"resource": res})
            alg_refs.append({"reference": f"AllergyIntolerance/{rid}"})

    # 3. Build Composition Sections
    sections = []
    
    # Medication Section
    sections.append({
        "title": "Medication Summary",
        "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_MEDICATIONS}]},
        "entry": med_refs if med_refs else [] # In real IPS, should handle empty reasons
    })
    
    # Allergies Section
    sections.append({
        "title": "Allergies and Intolerances",
        "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_ALLERGIES}]},
        "entry": alg_refs if alg_refs else []
    })

    # Problems Section
    sections.append({
        "title": "Problem List",
        "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_PROBLEMS}]},
        "entry": problem_refs if problem_refs else []
    })

    composition = create_composition(patient_id, practitioner_id, sections)

    # 4. Assemble Bundle
    # Order: Composition -> Patient -> Others
    bundle_entries = [{"resource": composition}, {"resource": patient}, {"resource": practitioner}]
    bundle_entries.extend(meds_entry)
    bundle_entries.extend(algs_entry)
    bundle_entries.extend(problems_entry)

    bundle = {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "document",
        "timestamp": datetime.now().isoformat(),
        "entry": [{"fullUrl": f"urn:uuid:{e['resource']['id']}", "resource": e['resource']} for e in bundle_entries]
    }
    
    return bundle

def main():
    print(f"Generating {RECORD_COUNT} IPS FHIR Bundles...")
    
    for i in range(RECORD_COUNT):
        bundle = generate_ips_bundle(i)
        filename = f"{OUTPUT_DIR}/ips_sample_{i:03d}.json"
        with open(filename, "w") as f:
            json.dump(bundle, f, indent=2)
            
    print(f"Done. Files saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
