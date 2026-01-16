import json
from typing import Any, Dict, Iterator, Optional
from .builder import IPSBuilder


class IPSGenerator:
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config: Dict[str, Any] = json.load(f)

    def generate_batch(
        self, count: int, seed: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        for i in range(count):
            record_seed = seed + i if seed is not None else None
            builder = IPSBuilder(self.config, seed=record_seed)

            rng = builder.rng

            # --- Randomly populate sections to create varied histories ---

            # 1. Conditions (50% chance for 1-3 conditions)
            if rng.random() > 0.2:
                for _ in range(rng.randint(1, 3)):
                    builder.add_condition()

            # 2. Medications (Matches conditions mostly)
            if rng.random() > 0.2:
                for _ in range(rng.randint(1, 3)):
                    builder.add_medication()

            # 3. Allergies (30% chance)
            if rng.random() > 0.7:
                builder.add_allergy()

            # 4. Immunizations (80% chance for 1-4 shots)
            if rng.random() > 0.2:
                for _ in range(rng.randint(1, 4)):
                    builder.add_immunization()

            # 5. Procedures (40% chance)
            if rng.random() > 0.6:
                builder.add_procedure()

            # 6. Medical Devices (10% chance)
            if rng.random() > 0.9:
                builder.add_medical_device()

            # 7. Lab Results (70% chance for 1-3 results)
            if rng.random() > 0.3:
                for _ in range(rng.randint(1, 3)):
                    builder.add_lab_result()

            yield builder.build()
