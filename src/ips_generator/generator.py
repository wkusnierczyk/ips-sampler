"""
IPS Generator Module.

This module provides the core functionality for generating synthetic International
Patient Summary (IPS) documents based on a provided configuration.
It orchestrates the creation of patient records using the IPSBuilder.
"""

import json
from typing import Any, Dict, Iterator, Optional
from .builder import IPSBuilder


class IPSGenerator:
    """
    Generator for International Patient Summary (IPS) FHIR Bundles.

    This class handles the loading of configuration data and the batch generation
    of synthetic patient records.

    Attributes:
        config (Dict[str, Any]): The loaded configuration dictionary containing
        clinical data and terminology definitions.
    """

    def __init__(self, config_path: str):
        """
        Initialize the IPSGenerator with a configuration file.

        Args:
            config_path (str): Path to the JSON configuration file containing
                demographics, clinical data options, and terminologies.
        """
        with open(config_path, "r") as f:
            self.config: Dict[str, Any] = json.load(f)

    def generate_batch(
        self, count: int, seed: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Generate a batch of synthetic IPS records.

        Args:
            count (int): The number of records to generate.
            seed (Optional[int]): An optional random seed for reproducibility.
                If provided, each record will be generated with a deterministic seed
                derived from this base seed.

        Yields:
            Iterator[Dict[str, Any]]: An iterator yielding generated FHIR Bundle
            resources as dictionaries.
        """
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
