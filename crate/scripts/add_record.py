#!/usr/bin/env python3
"""CLI tool to add a record to the Crate knowledge graph via Smart Add.

Usage:
    python scripts/add_record.py "Miles Davis" "Kind of Blue"
    python scripts/add_record.py "Fela Kuti" "Zombie" --user-id test-user
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.smart_add import search, research_and_ingest  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Add a record to Crate's knowledge graph")
    parser.add_argument("artist", help="Artist name")
    parser.add_argument("title", help="Album title")
    parser.add_argument("--user-id", default="cli-user", help="User ID (default: cli-user)")
    parser.add_argument("--auto", action="store_true", help="Auto-select first result")
    args = parser.parse_args()

    # Step 1: Search
    print(f"\nSearching for: {args.artist} - {args.title}")
    print("-" * 50)

    results = search(args.artist, args.title)

    if not results:
        print("No results found. Check the artist/title and try again.")
        return

    for i, r in enumerate(results):
        mb_tag = " [+MB]" if r.musicbrainz_id else ""
        print(f"  [{i + 1}] {r.title} ({r.year or '?'}) [{r.country or '?'}]{mb_tag}")

    if args.auto:
        choice = 0
    else:
        try:
            raw = input(f"\nSelect release [1-{len(results)}] (or 'q' to quit): ")
            if raw.lower() == "q":
                return
            choice = int(raw) - 1
        except (ValueError, EOFError):
            choice = 0

    selected = results[choice]
    print(f"\nSelected: {selected.title} (Discogs ID: {selected.discogs_id})")

    # Steps 2-5: Research and ingest
    print("\nResearching... (this may take a moment)")
    result = research_and_ingest(
        discogs_id=selected.discogs_id,
        musicbrainz_id=selected.musicbrainz_id,
        user_id=args.user_id,
    )

    # Display results
    print(f"\n{'=' * 50}")
    print(f"Added: {result.album_title}")
    print(f"Discogs ID: {result.discogs_id}")
    print(f"Artists/credits added: {result.artists_added}")

    synth = result.synthesized_data
    if synth.get("genres"):
        print(f"Genres: {', '.join(synth['genres'])}")
    if synth.get("scenes"):
        print(f"Scenes: {', '.join(s['name'] for s in synth['scenes'])}")
    if synth.get("studios"):
        print(f"Studios: {', '.join(s['name'] for s in synth['studios'])}")

    context = synth.get("context", {})
    if context.get("historical_note"):
        print(f"\nContext: {context['historical_note']}")
    if context.get("significance"):
        print(f"\nSignificance: {context['significance']}")

    if result.connections_found:
        print(f"\nNew connections in your graph:")
        for conn in result.connections_found:
            if conn["connection_type"] == "shared_artist":
                print(f"  - {conn['shared_artist']} also appears on: {', '.join(conn['also_on'])}")
            elif conn["connection_type"] == "shared_label":
                print(f"  - Label '{conn['shared_label']}' also on: {', '.join(conn['also_on'])}")
    else:
        print("\nNo new connections yet (add more records to see the graph light up!)")

    print("\nDone!")


if __name__ == "__main__":
    main()
