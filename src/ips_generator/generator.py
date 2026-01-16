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
            if rng.choice([True, False]):
                builder.add_condition()
            if rng.choice([True, False]):
                builder.add_medication()
            if rng.choice([True, False]):
                builder.add_allergy()

            yield builder.build()
