import unittest
import os
from ips_sampler.generator import IPSGenerator

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "ips_config.json"
)


class TestIPSGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = IPSGenerator(CONFIG_PATH)

    def test_record_count(self):
        count = 5
        results = list(self.generator.generate_batch(count))
        self.assertEqual(len(results), count)

    def test_bundle_structure(self):
        results = list(self.generator.generate_batch(1))
        bundle = results[0]
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "document")
        first_resource = bundle["entry"][0]["resource"]
        self.assertEqual(first_resource["resourceType"], "Composition")

    def test_reproducibility(self):
        seed = 42
        run_a = list(self.generator.generate_batch(1, seed=seed))[0]
        run_b = list(self.generator.generate_batch(1, seed=seed))[0]

        self.assertEqual(run_a["id"], run_b["id"])
        self.assertEqual(
            run_a["entry"][1]["resource"]["id"],
            run_b["entry"][1]["resource"]["id"]
        )


if __name__ == '__main__':
    unittest.main()
