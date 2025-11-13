import csv
import json
import logging
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List

import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {"json", "csv", "xml", "html", "excel"}

def _ensure_parent_dir(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

def _get_fieldnames(records: Iterable[Dict]) -> List[str]:
    fieldnames: List[str] = []
    for record in records:
        for key in record.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    return fieldnames

def export_json(records: List[Dict], output_path: Path) -> None:
    _ensure_parent_dir(output_path)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("JSON export completed: %s", output_path)

def export_csv(records: List[Dict], output_path: Path) -> None:
    _ensure_parent_dir(output_path)
    fieldnames = _get_fieldnames(records) if records else []
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    logger.info("CSV export completed: %s", output_path)

def export_xml(records: List[Dict], output_path: Path) -> None:
    _ensure_parent_dir(output_path)
    root = ET.Element("profiles")
    for record in records:
        item = ET.SubElement(root, "profile")
        for key, value in record.items():
            child = ET.SubElement(item, key)
            child.text = "" if value is None else str(value)

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    logger.info("XML export completed: %s", output_path)

def export_html(records: List[Dict], output_path: Path) -> None:
    _ensure_parent_dir(output_path)
    if records:
        headers = list(records[0].keys())
    else:
        headers = []

    lines: List[str] = []
    lines.append("<!DOCTYPE html>")
    lines.append("<html lang='en'>")
    lines.append("<head>")
    lines.append("  <meta charset='UTF-8' />")
    lines.append("  <title>WhatsApp Profiles Export</title>")
    lines.append("  <style>")
    lines.append("    table { border-collapse: collapse; width: 100%; }")
    lines.append("    th, td { border: 1px solid #ddd; padding: 8px; font-family: Arial, sans-serif; font-size: 14px; }")
    lines.append("    th { background-color: #f5f5f5; text-align: left; }")
    lines.append("    tr:nth-child(even) { background-color: #fafafa; }")
    lines.append("  </style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append("  <h1>WhatsApp Profiles Export</h1>")
    lines.append("  <table>")
    lines.append("    <thead>")
    lines.append("      <tr>")
    for h in headers:
        lines.append(f"        <th>{escape(str(h))}</th>")
    lines.append("      </tr>")
    lines.append("    </thead>")
    lines.append("    <tbody>")
    for record in records:
        lines.append("      <tr>")
        for h in headers:
            value = record.get(h, "")
            lines.append(f"        <td>{escape('' if value is None else str(value))}</td>")
        lines.append("      </tr>")
    lines.append("    </tbody>")
    lines.append("  </table>")
    lines.append("</body>")
    lines.append("</html>")

    _ensure_parent_dir(output_path)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("HTML export completed: %s", output_path)

def export_excel(records: List[Dict], output_path: Path) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # noqa: BLE001
        raise RuntimeError(
            "The 'openpyxl' package is required for Excel export. "
            "Install it with 'pip install openpyxl'."
        ) from exc

    _ensure_parent_dir(output_path)
    wb = Workbook()
    ws = wb.active
    ws.title = "Profiles"

    fieldnames = _get_fieldnames(records) if records else []
    if fieldnames:
        ws.append(fieldnames)
        for record in records:
            ws.append([record.get(field, "") for field in fieldnames])

    wb.save(output_path)
    logger.info("Excel export completed: %s", output_path)

def export_profiles(records: List[Dict], output_path: Path, fmt: str) -> None:
    fmt_normalized = fmt.lower()
    path = Path(output_path)

    if fmt_normalized not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported export format '{fmt}'. Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}")

    if fmt_normalized == "json":
        export_json(records, path)
    elif fmt_normalized == "csv":
        export_csv(records, path)
    elif fmt_normalized == "xml":
        export_xml(records, path)
    elif fmt_normalized == "html":
        export_html(records, path)
    elif fmt_normalized == "excel":
        # Ensure file has .xlsx extension for Excel
        if path.suffix.lower() != ".xlsx":
            path = path.with_suffix(".xlsx")
        export_excel(records, path)
    else:
        raise ValueError(f"Unexpected export format '{fmt_normalized}'.")