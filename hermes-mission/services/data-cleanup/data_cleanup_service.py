#!/usr/bin/env python3
"""
Mr Bubba Services - Automated Data Cleanup Pipeline
Accepts messy CSV/Excel/text files, cleans them automatically,
and generates a detailed cleanup report.
"""

import os
import re
import sys
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# ============================================================
# CONFIGURATION
# ============================================================
SERVICE_NAME = "Mr Bubba Data Cleanup Service"
SERVICE_VERSION = "1.0.0"
SERVICE_EMAIL = "mrbubba@agentmail.to"
SERVICE_PRICE = 75.00  # USD per file

# Directories
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"

for d in [INPUT_DIR, OUTPUT_DIR, REPORT_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "cleanup.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("mr-bubba-cleanup")


# ============================================================
# FILE LOADING
# ============================================================
def load_file(filepath: Path) -> Optional[pd.DataFrame]:
    """Load CSV, Excel, or text file into DataFrame."""
    ext = filepath.suffix.lower()
    try:
        if ext == ".csv":
            # Try common encodings
            for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    # Use on_bad_lines='warn' to skip malformed rows instead of failing
                    df = pd.read_csv(filepath, encoding=enc, on_bad_lines="warn")
                    logger.info(f"Loaded CSV with {enc}: {filepath.name} ({len(df)} rows)")
                    return df
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"CSV parse with {enc} failed: {e}")
                    continue
            # Fallback: try with Python engine and error handling
            try:
                df = pd.read_csv(
                    filepath,
                    encoding="utf-8",
                    on_bad_lines="skip",
                    engine="python",
                )
                logger.info(f"Loaded CSV (Python engine, skip bad lines): {filepath.name}")
                return df
            except Exception as e:
                logger.error(f"All CSV loading attempts failed: {e}")
                return None
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(filepath, engine="openpyxl")
            logger.info(f"Loaded Excel: {filepath.name}")
            return df
        elif ext == ".txt":
            # Try tab-separated first, then comma, then whitespace
            for sep in ["\t", ",", r"\s+"]:
                try:
                    df = pd.read_csv(filepath, sep=sep)
                    if len(df.columns) > 1:
                        logger.info(f"Loaded TXT (sep={repr(sep)}): {filepath.name}")
                        return df
                except Exception:
                    continue
            # Fallback: read as single column
            df = pd.read_csv(filepath, header=None, names=["data"])
            logger.info(f"Loaded TXT (single column): {filepath.name}")
            return df
        else:
            logger.error(f"Unsupported file format: {ext}")
            return None
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        return None


# ============================================================
# CLEANING FUNCTIONS
# ============================================================
def trim_whitespace(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Trim whitespace from all string columns. Returns (df, count_of_changes)."""
    count = 0
    for col in df.select_dtypes(include=["object", "string"]).columns:
        original = df[col].copy()
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("nan", np.nan)
        df[col] = df[col].replace("", np.nan)
        count += (original != df[col]).sum()
    logger.info(f"Trimmed whitespace: {count} cells affected")
    return df, count


def remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove exact duplicate rows."""
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = before - len(df)
    logger.info(f"Removed {removed} duplicate rows")
    return df, removed


def remove_fuzzy_duplicates(df: pd.DataFrame, threshold: float = 0.9) -> tuple[pd.DataFrame, int]:
    """Remove near-duplicate rows based on normalized string comparison."""
    before = len(df)
    # Normalize all string columns for comparison
    normalized = df.copy()
    for col in normalized.select_dtypes(include=["object", "string"]).columns:
        normalized[col] = (
            normalized[col]
            .astype(str)
            .str.lower()
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
        )
    # Use normalized data for dedup
    dup_mask = normalized.duplicated(keep="first")
    df = df[~dup_mask].reset_index(drop=True)
    removed = before - len(df)
    logger.info(f"Removed {removed} fuzzy duplicates (threshold={threshold})")
    return df, removed


def standardize_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Auto-detect date columns and standardize to YYYY-MM-DD format."""
    count = 0
    date_patterns = [
        r"\d{1,2}/\d{1,2}/\d{2,4}",     # MM/DD/YYYY or DD/MM/YYYY
        r"\d{1,2}-\d{1,2}-\d{2,4}",      # MM-DD-YYYY
        r"\d{4}/\d{1,2}/\d{1,2}",         # YYYY/MM/DD
        r"\d{4}-\d{1,2}-\d{1,2}",         # YYYY-MM-DD
        r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}",  # 1 January 2024
        r"[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}",  # January 1, 2024
    ]

    for col in df.columns:
        # Skip if already datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue

        # Check if column name suggests date
        col_lower = col.lower().strip()
        is_date_col = any(kw in col_lower for kw in ["date", "time", "day", "created", "updated", "dob", "birth"])

        if df[col].dtype == "object" or is_date_col:
            # Sample non-null values to check if they look like dates
            sample = df[col].dropna().astype(str).head(20)
            date_like = 0
            for val in sample:
                for pattern in date_patterns:
                    if re.match(pattern, val.strip()):
                        date_like += 1
                        break

            # If majority looks like dates or column name suggests date
            if date_like > len(sample) * 0.5 or (is_date_col and date_like > 0):
                try:
                    original = df[col].copy()
                    # Try multiple date formats
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    # Format as YYYY-MM-DD
                    df[col] = df[col].dt.strftime("%Y-%m-%d")
                    df[col] = df[col].replace("NaT", np.nan)
                    changed = (original.astype(str) != df[col].astype(str)).sum()
                    count += changed
                    logger.info(f"Standardized dates in '{col}': {changed} values")
                except Exception as e:
                    logger.warning(f"Could not parse dates in '{col}': {e}")

    return df, count


def standardize_phones(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Standardize phone numbers to +1-XXX-XXX-XXXX format (US) or (XXX) XXX-XXXX."""
    count = 0
    for col in df.columns:
        col_lower = col.lower().strip()
        if any(kw in col_lower for kw in ["phone", "tel", "mobile", "cell", "fax"]):
            if df[col].dtype == "object":
                original = df[col].copy()
                df[col] = df[col].astype(str).apply(_format_phone)
                df[col] = df[col].replace("nan", np.nan)
                changed = (original != df[col]).sum()
                count += changed
                logger.info(f"Standardized phones in '{col}': {changed} values")
    return df, count


def _format_phone(val: str) -> str:
    """Format a phone number string."""
    if pd.isna(val) or val in ["nan", "None", ""]:
        return val
    digits = re.sub(r"\D", "", str(val))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) == 12 and digits[0] == "+":
        return f"+{digits[1:2]} ({digits[2:5]}) {digits[5:8]}-{digits[8:]}"
    elif len(digits) > 0:
        return f"+{digits[:-10]} ({digits[-10:-7]}) {digits[-7:-4]}-{digits[-4:]}"
    return val


def standardize_addresses(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Standardize US address abbreviations and formatting."""
    count = 0
    usps_abbreviations = {
        r"\bst\.?\b": "St",
        r"\bave\.?\b": "Ave",
        r"\bblvd\.?\b": "Blvd",
        r"\bdr\.?\b": "Dr",
        r"\brd\.?\b": "Rd",
        r"\bct\.?\b": "Ct",
        r"\bpl\.?\b": "Pl",
        r"\bln\.?\b": "Ln",
        r"\bway\b": "Way",
        r"\bpkwy\.?\b": "Pkwy",
        r"\bhwy\.?\b": "Hwy",
        r"\bste\.?\b": "Ste",
        r"\bapt\.?\b": "Apt",
        r"\bn\.?\b": "N",
        r"\bs\.?\b": "S",
        r"\be\.?\b": "E",
        r"\bw\.?\b": "W",
        r"\bne\.?\b": "NE",
        r"\bnw\.?\b": "NW",
        r"\bse\.?\b": "SE",
        r"\bsw\.?\b": "SW",
    }

    state_abbreviations = {
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
        "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
        "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
        "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
        "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
        "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
        "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
        "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
        "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
        "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
        "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
        "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
        "wisconsin": "WI", "wyoming": "WY",
    }

    for col in df.columns:
        col_lower = col.lower().strip()
        if any(kw in col_lower for kw in ["address", "addr", "street", "city", "state", "zip"]):
            if df[col].dtype == "object":
                original = df[col].copy()
                # Apply USPS abbreviations
                for pattern, replacement in usps_abbreviations.items():
                    df[col] = df[col].astype(str).str.replace(
                        pattern, replacement, regex=True, case=False
                    )
                # Expand state names to abbreviations (for state columns)
                if "state" in col_lower:
                    for state_name, abbr in state_abbreviations.items():
                        df[col] = df[col].astype(str).str.replace(
                            rf"\b{state_name}\b", abbr, regex=True, case=False
                        )
                # Title case addresses
                if "address" in col_lower or "street" in col_lower:
                    df[col] = df[col].astype(str).str.title()
                # Clean up zip codes (5-digit or ZIP+4)
                if "zip" in col_lower:
                    df[col] = df[col].astype(str).str.extract(r"(\d{5}(?:-\d{4})?)")

                df[col] = df[col].replace("Nan", np.nan)
                changed = (original != df[col]).sum()
                count += changed
                if changed > 0:
                    logger.info(f"Standardized addresses in '{col}': {changed} values")

    return df, count


def add_calculations(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Add useful calculations for numeric columns."""
    calculations = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) > 0:
        # Add summary statistics row at bottom
        summary = {}
        for col in numeric_cols:
            summary[col] = {
                "sum": df[col].sum(),
                "mean": round(df[col].mean(), 2),
                "median": round(df[col].median(), 2),
                "min": df[col].min(),
                "max": df[col].max(),
                "std": round(df[col].std(), 2),
            }
        calculations.append(("numeric_summary", summary))
        logger.info(f"Added numeric summaries for {len(numeric_cols)} columns")

    # Add row count and null percentage
    null_pct = round((df.isnull().sum() / len(df) * 100), 2) if len(df) > 0 else 0
    calculations.append(("null_percentages", null_pct.to_dict()))

    # Add data quality score
    total_cells = df.size
    null_cells = df.isnull().sum().sum()
    dup_score = 1.0  # Already removed dups
    quality_score = round(((total_cells - null_cells) / total_cells) * 100, 1) if total_cells > 0 else 0
    calculations.append(("data_quality_score", {
        "score": quality_score,
        "total_cells": total_cells,
        "null_cells": null_cells,
        "completeness": f"{quality_score}%",
    }))
    logger.info(f"Data quality score: {quality_score}%")

    return df, calculations


def remove_empty_rows_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove completely empty rows and columns."""
    empty_rows = df.isnull().all(axis=1).sum()
    empty_cols = df.isnull().all(axis=0).sum()
    df = df.dropna(how="all").reset_index(drop=True)
    df = df.dropna(axis=1, how="all")
    logger.info(f"Removed {empty_rows} empty rows, {empty_cols} empty columns")
    return df, {"empty_rows_removed": int(empty_rows), "empty_cols_removed": int(empty_cols)}


def normalize_headers(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Normalize column headers: lowercase, underscores, no special chars."""
    count = 0
    new_cols = {}
    for col in df.columns:
        new_col = str(col).strip().lower()
        new_col = re.sub(r"[^a-z0-9_]", "_", new_col)
        re.sub(r"_+", "_", new_col)
        new_col = new_col.strip("_")
        if new_col != str(col):
            new_cols[col] = new_col
            count += 1
    if new_cols:
        df = df.rename(columns=new_cols)
        logger.info(f"Normalized {count} column headers: {new_cols}")
    return df, count


# ============================================================
# MAIN CLEANUP PIPELINE
# ============================================================
def clean_data(filepath: Path) -> dict:
    """Run the full cleanup pipeline on a file."""
    logger.info(f"{'='*60}")
    logger.info(f"Processing: {filepath.name}")
    logger.info(f"{'='*60}")

    # Load file
    df = load_file(filepath)
    if df is None:
        return {"success": False, "error": "Failed to load file"}

    # Initial stats
    original_rows = len(df)
    original_cols = len(df.columns)
    original_cells = df.size
    original_nulls = int(df.isnull().sum().sum())
    original_dups = int(df.duplicated().sum())

    report = {
        "filename": filepath.name,
        "original_rows": original_rows,
        "original_cols": original_cols,
        "original_cells": original_cells,
        "original_nulls": original_nulls,
        "original_duplicates": original_dups,
        "steps": [],
    }

    # Step 1: Normalize headers
    df, header_count = normalize_headers(df)
    report["steps"].append({"step": "normalize_headers", "columns_renamed": header_count})

    # Step 2: Trim whitespace
    df, ws_count = trim_whitespace(df)
    report["steps"].append({"step": "trim_whitespace", "cells_trimmed": ws_count})

    # Step 3: Remove duplicates
    df, exact_dups = remove_duplicates(df)
    report["steps"].append({"step": "remove_duplicates", "rows_removed": exact_dups})

    # Step 4: Remove fuzzy duplicates
    df, fuzzy_dups = remove_fuzzy_duplicates(df)
    report["steps"].append({"step": "remove_fuzzy_duplicates", "rows_removed": fuzzy_dups})

    # Step 5: Remove empty rows/columns
    df, empty_removed = remove_empty_rows_columns(df)
    report["steps"].append({"step": "remove_empty", **empty_removed})

    # Step 6: Standardize dates
    df, date_count = standardize_dates(df)
    report["steps"].append({"step": "standardize_dates", "values_standardized": date_count})

    # Step 7: Standardize phones
    df, phone_count = standardize_phones(df)
    report["steps"].append({"step": "standardize_phones", "values_standardized": phone_count})

    # Step 8: Standardize addresses
    df, addr_count = standardize_addresses(df)
    report["steps"].append({"step": "standardize_addresses", "values_standardized": addr_count})

    # Step 9: Add calculations
    df, calculations = add_calculations(df)
    report["calculations"] = calculations

    # Final stats
    report["final_rows"] = len(df)
    report["final_cols"] = len(df.columns)
    report["final_cells"] = df.size
    report["final_nulls"] = int(df.isnull().sum().sum())

    # Save cleaned file
    output_path = OUTPUT_DIR / f"cleaned_{filepath.stem}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Saved cleaned file: {output_path}")

    # Save report
    report_path = REPORT_DIR / f"report_{filepath.stem}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Saved report: {report_path}")

    report["success"] = True
    report["output_file"] = str(output_path)
    report["report_file"] = str(report_path)
    return report


def generate_text_report(report: dict) -> str:
    """Generate a human-readable text report."""
    lines = [
        "=" * 60,
        f"  {SERVICE_NAME} - Cleanup Report",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
        f"File: {report.get('filename', 'Unknown')}",
        "",
        "--- Summary ---",
        f"  Original rows:    {report.get('original_rows', 0):,}",
        f"  Original columns: {report.get('original_cols', 0):,}",
        f"  Original nulls:   {report.get('original_nulls', 0):,}",
        f"  Original dupes:   {report.get('original_duplicates', 0):,}",
        "",
        f"  Cleaned rows:     {report.get('final_rows', 0):,}",
        f"  Cleaned columns:  {report.get('final_cols', 0):,}",
        f"  Cleaned nulls:    {report.get('final_nulls', 0):,}",
        "",
        "--- Steps Performed ---",
    ]
    for step in report.get("steps", []):
        step_name = step["step"].replace("_", " ").title()
        details = {k: v for k, v in step.items() if k != "step"}
        lines.append(f"  ✓ {step_name}: {details}")

    lines.append("")
    lines.append("--- Data Quality ---")
    for calc_name, calc_data in report.get("calculations", []):
        if calc_name == "data_quality_score":
            lines.append(f"  Quality Score: {calc_data.get('score', 'N/A')}%")
            lines.append(f"  Completeness: {calc_data.get('completeness', 'N/A')}")
        elif calc_name == "numeric_summary":
            lines.append("  Numeric Column Summaries:")
            for col, stats in calc_data.items():
                lines.append(f"    {col}: sum={stats['sum']}, mean={stats['mean']}, min={stats['min']}, max={stats['max']}")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Service Price: ${SERVICE_PRICE:.2f}")
    lines.append(f"  Invoice via PayPal: {SERVICE_EMAIL}")
    lines.append("=" * 60)

    return "\n".join(lines)


# ============================================================
# CLI ENTRY POINT
# ============================================================
def main():
    """CLI entry point for the cleanup service."""
    import argparse

    parser = argparse.ArgumentParser(description="Mr Bubba Data Cleanup Service")
    parser.add_argument("file", help="Path to CSV/Excel/text file to clean")
    parser.add_argument("--output-dir", "-o", help="Output directory", default=None)
    parser.add_argument("--report-format", "-r", choices=["json", "text", "both"], default="both")
    parser.add_argument("--fuzzy-threshold", "-f", type=float, default=0.9)
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        sys.exit(1)

    if args.output_dir:
        global OUTPUT_DIR, REPORT_DIR
        OUTPUT_DIR = Path(args.output_dir)
        REPORT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = clean_data(filepath)

    if not report["success"]:
        logger.error("Cleanup failed")
        sys.exit(1)

    # Generate text report
    if args.report_format in ["text", "both"]:
        text_report = generate_text_report(report)
        text_path = REPORT_DIR / f"report_{filepath.stem}.txt"
        with open(text_path, "w") as f:
            f.write(text_report)
        print(text_report)
        logger.info(f"Saved text report: {text_path}")

    if args.report_format in ["json", "both"]:
        logger.info(f"JSON report: {report.get('report_file', 'N/A')}")

    print(f"\n✅ Cleanup complete! Cleaned file saved to: {report['output_file']}")
    print(f"📄 Service price: ${SERVICE_PRICE:.2f} (invoice via PayPal: {SERVICE_EMAIL})")


if __name__ == "__main__":
    main()
