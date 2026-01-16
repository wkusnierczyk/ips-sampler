import argparse
import sys
import json
import os
import logging
from typing import Optional
from ips_generator.generator import IPSGenerator
from ips_generator.renderer import IPSPDFRenderer
from ips_generator import __version__

# Configure Logging to explicitly use stderr
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr
)
logger = logging.getLogger("ips-generator")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic IPS FHIR Bundles.")

    # Arguments
    parser.add_argument(
        "-p", "--patients", type=int, help="Number of unique patients to generate"
    )

    parser.add_argument(
        "-r",
        "--repeats",
        type=int,
        default=1,
        help="Number of records to generate per patient (default: 1)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save output files",
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
        "--pdf",
        action="store_true",
        help="Generate PDF version of the records alongside JSON",
    )

    parser.add_argument(
        "--about", action="store_true", help="Show tool information and exit"
    )

    args = parser.parse_args()

    # Handle --about
    if args.about:
        print(
            "ips-generator: Synthetic International " "Patient Summary (IPS) Generator"
        )
        print(f"├─ version: {__version__}")
        print("├─ developer: mailto:waclaw.kusnierczyk@gmail.com")
        print("├─ source: https://github.com/wkusnierczyk/ips-sampler")
        print("└─ licence: MIT https://opensource.org/licenses/MIT")
        sys.exit(0)

    # Validate required args
    if not args.patients:
        parser.error("the following arguments are required: -p/--patients")

    if not os.path.exists(args.config):
        logger.error(f"Config file not found at {args.config}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    try:
        gen = IPSGenerator(args.config)
        renderer = IPSPDFRenderer() if args.pdf else None

        total_files = args.patients * args.repeats
        logger.info(
            f"Generating {total_files} records "
            f"({args.patients} patients x {args.repeats} repeats)..."
        )

        for bundle, p_idx, r_idx in gen.generate_batch(
            args.patients, args.repeats, args.seed
        ):
            # Filename structure: patient_XXX_record_YY.json
            base_filename = f"patient_{p_idx:03d}_record_{r_idx:02d}"

            # 1. Save JSON
            json_path = os.path.join(args.output_dir, f"{base_filename}.json")
            with open(json_path, "w") as f:
                indent: Optional[int] = None if args.minify else 2
                json.dump(bundle, f, indent=indent)

            # 2. Save PDF (if requested)
            if renderer:
                pdf_path = os.path.join(args.output_dir, f"{base_filename}.pdf")
                renderer.render_to_file(bundle, pdf_path)

        logger.info(f"Successfully generated files in '{args.output_dir}'")

    except Exception:
        logger.exception("An unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
