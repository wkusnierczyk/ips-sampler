import unittest
import os
import tempfile
from ips_generator.generator import IPSGenerator
from ips_generator.renderer import IPSPDFRenderer

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "ips_config.json")


class TestIPSGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = IPSGenerator(CONFIG_PATH)

    def test_record_count(self):
        """Verify total number of records matches patients * repeats."""
        patients = 2
        repeats = 3
        results = list(self.generator.generate_batch(patients, repeats))
        self.assertEqual(len(results), patients * repeats)

    def test_bundle_structure(self):
        """Verify basic FHIR Bundle / Document structure."""
        results = list(self.generator.generate_batch(1, 1))
        bundle = results[0][0]
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "document")

        # First entry must be Composition
        first_resource = bundle["entry"][0]["resource"]
        self.assertEqual(first_resource["resourceType"], "Composition")

    def test_patient_identity_persistence(self):
        """
        Verify that multiple records for the same patient share demographics
        but have unique bundle IDs.
        """
        patients = 1
        repeats = 2
        results = list(self.generator.generate_batch(patients, repeats))

        bundle_1 = results[0][0]
        bundle_2 = results[1][0]

        # Extract Patient Resources
        pat_1 = self._find_resource(bundle_1, "Patient")
        pat_2 = self._find_resource(bundle_2, "Patient")

        # Identity must match
        self.assertEqual(pat_1["id"], pat_2["id"])
        self.assertEqual(pat_1["name"][0]["family"], pat_2["name"][0]["family"])
        self.assertEqual(pat_1["birthDate"], pat_2["birthDate"])

        # Documents must differ
        self.assertNotEqual(bundle_1["id"], bundle_2["id"])

    def test_clinical_content_diversity(self):
        """
        Probabilistic test: Generate a batch and ensure we see varied resource types.
        (It is statistically impossible for 50 records to have NO meds/labs/etc)
        """
        results = list(self.generator.generate_batch(50, 1, seed=123))

        counts = {
            "MedicationStatement": 0,
            "Condition": 0,
            "AllergyIntolerance": 0,
            "Immunization": 0,
            "Procedure": 0,
            "Observation": 0,
            "Device": 0,
        }

        for bundle, _, _ in results:
            for entry in bundle.get("entry", []):
                rtype = entry["resource"]["resourceType"]
                if rtype in counts:
                    counts[rtype] += 1

        # Assert we found at least one of each (given the probabilities in generator.py)
        for rtype, count in counts.items():
            self.assertGreater(
                count, 0, f"Generated 50 records but found 0 {rtype}s. Check RNG logic."
            )

    def test_composition_integrity(self):
        """Ensure every clinical resource is referenced in the Composition sections."""
        results = list(self.generator.generate_batch(1, 1, seed=42))
        bundle = results[0][0]

        composition = bundle["entry"][0]["resource"]

        # Gather all references from Composition sections
        referenced_ids = set()
        for section in composition.get("section", []):
            for entry in section.get("entry", []):
                ref = entry["reference"]  # e.g., "Condition/uuid..."
                referenced_ids.add(ref)

        # Check that every clinical resource in the bundle is referenced
        for entry in bundle["entry"][1:]:  # Skip Composition itself
            res = entry["resource"]
            rtype = res["resourceType"]

            # Skip Patient/Practitioner as they are referenced in header, not sections
            if rtype in ["Patient", "Practitioner"]:
                continue

            full_ref = f"{rtype}/{res['id']}"
            self.assertIn(
                full_ref,
                referenced_ids,
                f"Resource {full_ref} exists but is orphaned (not in Composition).",
            )

    def test_pdf_renderer_smoke(self):
        """Ensure PDF generation runs without crashing."""
        results = list(self.generator.generate_batch(1, 1))
        bundle = results[0][0]

        renderer = IPSPDFRenderer()

        # Create a temp file to render to
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            try:
                tmp.close()  # Close so reportlab can write to it
                renderer.render_to_file(bundle, tmp.name)

                # Check if file exists and has size
                self.assertTrue(os.path.exists(tmp.name))
                self.assertGreater(os.path.getsize(tmp.name), 0)
            finally:
                if os.path.exists(tmp.name):
                    os.remove(tmp.name)

    def _find_resource(self, bundle, resource_type):
        for entry in bundle["entry"]:
            if entry["resource"]["resourceType"] == resource_type:
                return entry["resource"]
        return None


if __name__ == "__main__":
    unittest.main()
