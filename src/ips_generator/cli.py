"""
Command Line Interface for IPS Generator.

This module provides the entry point for the command-line tool. It parses arguments,
sets up logging, and invokes the IPSGenerator to create synthetic records.
"""

import argparse
import sys
import json
import os
import logging
from typing import Optional
from ips_generator.generator import IPSGenerator
from ips_generator import __version__

# Configure Logging to explicitly use stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,  # Explicitly send logs to stderr
)
logger = logging.getLogger("ips-generator")


def main() -> None:
    """
    Main entry point for the CLI.

    Parses command line arguments for sample count, output directory, configuration
    file, and seed. Generates the requested number of IPS records and saves them as
    JSON files.
    """
    parser = argparse.ArgumentParser(description="Generate synthetic IPS FHIR Bundles.")

    # Arguments
    parser.add_argument(
        "-s", "--samples", type=int, help="Number of samples to generate"
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save JSON files",
    )

    default_config = "config/ips_config.json"
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=default_config,
        help="Path to JSON configuration file",
    )

    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")

    parser.add_argument("--minify", action="store_true", help="Output minified JSON")

    parser.add_argument(
        "--about", action="store_true", help="Show tool information and exit"
    )

    args = parser.parse_args()

    # Handle --about (This goes to stdout as it is the requested output)
    if args.about:
        print("ips-generator: Synthetic International Patient Summary (IPS) Generator")
        print(f"├─ version:   {__version__}")
        print("├─ developer: mailto:waclaw.kusnierczyk@gmail.com")
        print("├─ source:    https://github.com/wkusnierczyk/ips-sampler")
        print("└─ licence:   MIT https://opensource.org/licenses/MIT")
        sys.exit(0)

    # Validate required args
    if not args.samples:
        parser.error("the following arguments are required: -s/--samples")

    if not os.path.exists(args.config):
        logger.error(f"Config file not found at {args.config}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    try:
        gen = IPSGenerator(args.config)
        logger.info(f"Generating {args.samples} records...")

        for i, bundle in enumerate(gen.generate_batch(args.samples, args.seed)):
            filename = os.path.join(args.output_dir, f"ips_record_{i:04d}.json")
            with open(filename, "w") as f:
                indent: Optional[int] = None if args.minify else 2
                json.dump(bundle, f, indent=indent)

        logger.info(
            f"Successfully generated {args.samples} files " f"in '{args.output_dir}'"
        )

    except Exception:
        logger.exception("An unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
