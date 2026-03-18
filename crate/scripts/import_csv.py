#!/usr/bin/env python3
"""Import a Discogs collection from CSV export.

Export your collection from: Discogs > Settings > Collection > Export

Usage:
    python scripts/import_csv.py collection.csv
    python scripts/import_csv.py collection.csv --quick          # Fast, basic import (no AI research)
    python scripts/import_csv.py collection.csv --user-id lucas  # Specify user
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.discogs_csv import parse_csv, import_collection_from_csv  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Import Discogs collection from CSV")
    parser.add_argument("csv_file", help="Path to Discogs CSV export")
    parser.add_argument("--user-id", default="cli-user", help="User ID for ownership")
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick import: basic data only, no AI research (fast, can enrich later)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse CSV and show records without importing")
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        sys.exit(1)

    if args.dry_run:
        records = parse_csv(file_path=csv_path)
        print(f"\nFound {len(records)} records in CSV:\n")
        for i, r in enumerate(records, 1):
            print(f"  {i:3d}. {r.artist} - {r.title} ({r.released or '?'}) [{r.label}] Discogs:{r.release_id}")
        print(f"\nTotal: {len(records)} records")
        print("Run without --dry-run to import.")
        return

    mode = "quick (basic data, no AI)" if args.quick else "full (AI research per record — slow)"
    records = parse_csv(file_path=csv_path)
    print(f"\nImporting {len(records)} records")
    print(f"Mode: {mode}")
    print(f"User: {args.user_id}")
    print("=" * 50)

    if not args.quick and len(records) > 10:
        print(f"\nFull mode will make ~3 API calls per record ({len(records) * 3}+ total).")
        print("This may take a while. Consider --quick for initial import, then enrich later.")
        confirm = input("Continue? [y/N] ")
        if confirm.lower() != "y":
            return

    summary = import_collection_from_csv(
        file_path=csv_path,
        user_id=args.user_id,
        skip_research=args.quick,
    )

    print(f"\n{'=' * 50}")
    print(f"Import complete!")
    print(f"  Total in CSV: {summary['total_in_csv']}")
    print(f"  Imported: {summary['imported']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Mode: {summary['mode']}")

    if args.quick:
        print(f"\nBasic graph created. To enrich with AI research, run:")
        print(f"  python scripts/enrich_collection.py --user-id {args.user_id}")


if __name__ == "__main__":
    main()
