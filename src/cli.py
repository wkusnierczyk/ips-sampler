import argparse
import sys
import json
import os
from ips_gen.generator import IPSGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic IPS FHIR Bundles.")

    # Required
    parser.add_argument(
        "-s", "--samples", type=int, required=True, help="Number of samples to generate"
    )

    # Optional
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save JSON files",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config/ips_config.json",
        help="Path to JSON configuration file",
    )
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument(
        "--minify", action="store_true", help="Output minified JSON (no indentation)"
    )

    args = parser.parse_args()

    # Validation
    if not os.path.exists(args.config):
        print(f"Error: Config file not found at {args.config}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Execution
    try:
        gen = IPSGenerator(args.config)
        print(f"Generating {args.samples} records...")

        for i, bundle in enumerate(gen.generate_batch(args.samples, args.seed)):
            filename = os.path.join(args.output_dir, f"ips_record_{i:04d}.json")

            with open(filename, "w") as f:
                indent = None if args.minify else 2
                json.dump(bundle, f, indent=indent)

        print(f"Successfully generated {args.samples} files in '{args.output_dir}'")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
