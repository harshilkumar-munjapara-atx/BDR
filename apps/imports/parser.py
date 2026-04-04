"""
Excel import parser.

Expected columns (case-insensitive, whitespace-trimmed):
  company_name, sector, company_type, founded_year, headcount_range,
  website, linkedin, primary_email, primary_phone, hq_country, hq_city,
  regions_served (comma-separated), description, revenue_range,
  funding_stage, business_type_tags (comma-separated),
  products (pipe-separated: name|description|category),
  key_people (pipe-separated: name|title|linkedin)
"""
import io
from dataclasses import dataclass, field
from typing import Any

import openpyxl

REQUIRED_COLUMNS = {"company_name", "primary_email", "hq_country"}

MAX_ROWS = 500


@dataclass
class ParsedRow:
    row_number: int
    data: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)

    @property
    def is_valid(self):
        return not self.errors


def _split(value: str, sep: str) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(sep) if v.strip()]


def _parse_products(raw: str) -> list[dict]:
    products = []
    for entry in _split(raw, ";"):
        parts = [p.strip() for p in entry.split("|")]
        products.append({
            "name": parts[0] if len(parts) > 0 else "",
            "short_description": parts[1] if len(parts) > 1 else "",
            "category_tag": parts[2] if len(parts) > 2 else "",
        })
    return products


def _parse_key_people(raw: str) -> list[dict]:
    people = []
    for i, entry in enumerate(_split(raw, ";")):
        parts = [p.strip() for p in entry.split("|")]
        people.append({
            "full_name": parts[0] if len(parts) > 0 else "",
            "job_title": parts[1] if len(parts) > 1 else "",
            "linkedin_url": parts[2] if len(parts) > 2 else "",
            "display_order": i,
        })
    return people


def parse_excel(file_bytes: bytes) -> tuple[list[ParsedRow], list[str]]:
    """
    Parse an Excel file and return (rows, global_errors).
    rows: list of ParsedRow (valid and invalid)
    global_errors: file-level errors (wrong format, too many rows, missing columns)
    """
    global_errors = []
    rows = []

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:
        return [], [f"Could not open file: {exc}"]

    ws = wb.active
    raw_rows = list(ws.iter_rows(values_only=True))
    if not raw_rows:
        return [], ["File is empty."]

    headers = [str(h).strip().lower() if h is not None else "" for h in raw_rows[0]]
    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        return [], [f"Missing required columns: {', '.join(sorted(missing))}"]

    data_rows = raw_rows[1:]
    if len(data_rows) > MAX_ROWS:
        global_errors.append(f"File has {len(data_rows)} rows; maximum allowed is {MAX_ROWS}.")
        data_rows = data_rows[:MAX_ROWS]

    def col(row_values: tuple, name: str) -> str:
        try:
            idx = headers.index(name)
            val = row_values[idx]
            return str(val).strip() if val is not None else ""
        except (ValueError, IndexError):
            return ""

    seen_keys: set[tuple] = set()

    for i, row_values in enumerate(data_rows, start=2):
        parsed = ParsedRow(row_number=i)

        company_name = col(row_values, "company_name")
        primary_email = col(row_values, "primary_email")
        hq_country = col(row_values, "hq_country")

        if not company_name:
            parsed.errors.append("company_name is required.")
        if not primary_email:
            parsed.errors.append("primary_email is required.")
        if not hq_country:
            parsed.errors.append("hq_country is required.")

        dup_key = (company_name.lower(), hq_country.lower())
        if dup_key in seen_keys:
            parsed.errors.append(f"Duplicate entry: {company_name} / {hq_country}.")
        else:
            seen_keys.add(dup_key)

        founded_raw = col(row_values, "founded_year")
        founded_year = None
        if founded_raw:
            try:
                founded_year = int(float(founded_raw))
            except ValueError:
                parsed.errors.append(f"founded_year '{founded_raw}' is not a valid year.")

        parsed.data = {
            "identity": {
                "company_name": company_name,
                "tagline": col(row_values, "tagline"),
                "description": col(row_values, "description"),
                "company_type": col(row_values, "company_type"),
                "sector_tags": _split(col(row_values, "sector"), ","),
                "founded_year": founded_year,
                "headcount_range": col(row_values, "headcount_range"),
                "website_url": col(row_values, "website"),
                "linkedin_url": col(row_values, "linkedin"),
            },
            "contact": {
                "primary_email": primary_email,
                "primary_phone": col(row_values, "primary_phone"),
                "hq_country": hq_country,
                "hq_city": col(row_values, "hq_city"),
                "regions_served": _split(col(row_values, "regions_served"), ","),
            },
            "commercial": {
                "revenue_range": col(row_values, "revenue_range"),
                "funding_stage": col(row_values, "funding_stage"),
                "business_type_tags": _split(col(row_values, "business_type_tags"), ","),
            },
            "products": _parse_products(col(row_values, "products")),
            "key_people": _parse_key_people(col(row_values, "key_people")),
        }
        rows.append(parsed)

    return rows, global_errors
