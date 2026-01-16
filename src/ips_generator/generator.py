import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, Optional, Tuple
from .builder import IPSBuilder


class IPSGenerator:
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config: Dict[str, Any] = json.load(f)

    def generate_batch(
        self, patient_count: int, repeats: int = 1, seed: Optional[int] = None
    ) -> Iterator[Tuple[Dict[str, Any], int, int]]:
        """
        Generates batches of IPS records.

        Args:
            patient_count: Number of unique patients to simulate.
            repeats: Number of records to generate per patient.
            seed: Base random seed.

        Yields:
            Tuple containing:
            - The FHIR Bundle (dict)
            - Patient Index (int)
            - Record Index (int)
        """

        base_rng = random.Random(seed) if seed is not None else random.Random()

        for p_idx in range(patient_count):
            # 1. Establish Patient Identity (persists across repeats)
            # We generate specific attributes here to pass to the builder
            pat_seed = base_rng.randint(0, 2**32)
            pat_rng = random.Random(pat_seed)

            # Helper to pick random date
            def rand_date(rng: random.Random, start: int, end: int) -> str:
                return (
                    datetime.now() - timedelta(days=rng.randint(start, end))
                ).strftime("%Y-%m-%d")

            patient_context = {
                "id": str(uuid.UUID(int=pat_rng.getrandbits(128))),
                "family": pat_rng.choice(self.config["demographics"]["family_names"]),
                "given": pat_rng.choice(self.config["demographics"]["given_names"]),
                "birthDate": rand_date(pat_rng, 7000, 30000),
                "gender": pat_rng.choice(["male", "female", "other", "unknown"]),
            }

            # 2. Generate Records for this Patient
            for r_idx in range(repeats):
                # Unique seed for this specific record instance
                record_seed = base_rng.randint(0, 2**32)

                builder = IPSBuilder(
                    self.config, seed=record_seed, patient_context=patient_context
                )

                rng = builder.rng

                # --- Randomly populate sections ---
                if rng.random() > 0.2:
                    for _ in range(rng.randint(1, 3)):
                        builder.add_condition()

                if rng.random() > 0.2:
                    for _ in range(rng.randint(1, 3)):
                        builder.add_medication()

                if rng.random() > 0.7:
                    builder.add_allergy()

                if rng.random() > 0.2:
                    for _ in range(rng.randint(1, 4)):
                        builder.add_immunization()

                if rng.random() > 0.6:
                    builder.add_procedure()

                if rng.random() > 0.9:
                    builder.add_medical_device()

                if rng.random() > 0.3:
                    for _ in range(rng.randint(1, 3)):
                        builder.add_lab_result()

                yield builder.build(), p_idx, r_idx
