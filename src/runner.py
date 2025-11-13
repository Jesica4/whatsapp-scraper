import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from extractors.whatsapp_parser import build_profiles
from outputs.exporters import export_profiles, SUPPORTED_FORMATS

def load_settings(settings_path: Path) -> Dict[str, Any]:
    """
    Load JSON settings file if it exists, otherwise return sensible defaults.
    """
    defaults: Dict[str, Any] = {
        "default_output_format": "json",
        "media_base_url": "https://cdn.example.com/whatsapp/avatars",
        "rate_limit_per_minute": 600,
        "log_level": "INFO",
    }

    if not settings_path.is_file():
        return defaults

    try:
        with settings_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logging.warning("Settings file %s does not contain a JSON object, using defaults.", settings_path)
            return defaults
        merged = {**defaults, **data}
        return merged
    except Exception as exc:  # noqa: BLE001
        logging.warning("Failed to load settings from %s: %s. Using defaults.", settings_path, exc)
        return defaults

def configure_logging(level_name: str) -> None:
    """
    Configure root logger based on string level.
    """
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

def read_numbers_from_file(path: Path) -> List[str]:
    """
    Read phone numbers from a text file, one per line.
    Empty lines and comment lines starting with '#' are ignored.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")

    numbers: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            numbers.append(raw)

    if not numbers:
        raise ValueError(f"No valid phone numbers found in input file: {path}")

    return numbers

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent.parent  # whatsapp-scraper/
    default_input = base_dir / "data" / "inputs.sample.txt"
    default_output = base_dir / "data" / "sample.json"
    default_settings = base_dir / "src" / "config" / "settings.example.json"

    parser = argparse.ArgumentParser(
        description="WhatsApp Profiles Scraper - CLI Runner",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=str(default_input),
        help=f"Path to input file containing phone numbers (default: {default_input})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(default_output),
        help=f"Path to output file (default: {default_output})",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=sorted(SUPPORTED_FORMATS),
        help="Output format. Overrides config default_output_format.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=str(default_settings),
        help=f"Path to settings JSON (default: {default_settings})",
    )
    return parser.parse_args(argv)

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    settings_path = Path(args.config)
    settings = load_settings(settings_path)
    configure_logging(settings.get("log_level", "INFO"))

    logger = logging.getLogger("runner")

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Determine output format
    if args.format:
        output_format = args.format.lower()
    else:
        output_format = str(settings.get("default_output_format", "json")).lower()

    if output_format not in SUPPORTED_FORMATS:
        logger.error(
            "Unsupported output format '%s'. Supported formats: %s",
            output_format,
            ", ".join(sorted(SUPPORTED_FORMATS)),
        )
        return 1

    logger.info("Using settings from %s", settings_path)
    logger.info("Input file: %s", input_path)
    logger.info("Output file: %s", output_path)
    logger.info("Output format: %s", output_format)

    try:
        numbers = read_numbers_from_file(input_path)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read input file: %s", exc)
        return 1

    media_base_url = str(settings.get("media_base_url", "https://cdn.example.com/whatsapp/avatars"))
    rate_limit_per_minute = int(settings.get("rate_limit_per_minute", 600))

    logger.info("Loaded %d phone numbers from input.", len(numbers))
    logger.debug("Rate limit per minute configured as %d (not enforced in demo implementation).", rate_limit_per_minute)

    try:
        profiles = build_profiles(
            numbers=numbers,
            media_base_url=media_base_url,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to build profiles: %s", exc)
        return 1

    if not profiles:
        logger.warning("No profiles generated from input numbers.")
    else:
        logger.info("Generated %d profiles.", len(profiles))

    try:
        export_profiles(profiles, output_path, output_format)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to export profiles: %s", exc)
        return 1

    logger.info("Export completed successfully.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())