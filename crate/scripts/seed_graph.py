#!/usr/bin/env python3
"""Seed the Crate graph with a set of records to have a working graph for development.

Usage:
    python scripts/seed_graph.py
    python scripts/seed_graph.py --user-id my-user
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.smart_add import search, research_and_ingest  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# A curated set of records that create an interesting, connected graph.
# Chosen to have overlapping musicians, labels, scenes, and studios.
SEED_RECORDS = [
    ("Miles Davis", "Kind of Blue"),
    ("John Coltrane", "A Love Supreme"),
    ("Herbie Hancock", "Head Hunters"),
    ("Fela Kuti", "Zombie"),
    ("Art Blakey", "Moanin'"),
    ("Jorge Ben Jor", "A Tábua de Esmeralda"),
    ("Marcos Valle", "Previsão do Tempo"),
    ("Lee Morgan", "The Sidewinder"),
    ("Wayne Shorter", "Speak No Evil"),
    ("Tony Allen", "Jealousy"),
]


def main():
    parser = argparse.ArgumentParser(description="Seed the Crate graph with sample records")
    parser.add_argument("--user-id", default="seed-user", help="User ID for ownership")
    args = parser.parse_args()

    print(f"Seeding graph with {len(SEED_RECORDS)} records...")
    print(f"User ID: {args.user_id}")
    print("=" * 50)

    for i, (artist, title) in enumerate(SEED_RECORDS, 1):
        print(f"\n[{i}/{len(SEED_RECORDS)}] {artist} - {title}")

        try:
            results = search(artist, title)
            if not results:
                print("  SKIP: No results found")
                continue

            selected = results[0]
            print(f"  Found: {selected.title} (Discogs: {selected.discogs_id})")

            result = research_and_ingest(
                discogs_id=selected.discogs_id,
                musicbrainz_id=selected.musicbrainz_id,
                user_id=args.user_id,
            )

            print(f"  Added {result.artists_added} artists/credits")
            if result.connections_found:
                print(f"  {len(result.connections_found)} new connections found!")

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    print(f"\n{'=' * 50}")
    print("Seed complete! Open Neo4j Browser at http://localhost:7474 to explore the graph.")
    print("Try: MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100")


if __name__ == "__main__":
    main()
