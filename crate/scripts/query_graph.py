#!/usr/bin/env python3
"""CLI tool to query the Crate knowledge graph with natural language.

Usage:
    python scripts/query_graph.py "What connects my Brazilian records to my jazz records?"
    python scripts/query_graph.py "Who appears on the most albums in my collection?"
    python scripts/query_graph.py --stats
    python scripts/query_graph.py --connections 12345 67890  (two discogs IDs)
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.graph.connection import get_neo4j_driver, close_neo4j_driver  # noqa: E402
from app.graph.queries import get_user_collection, get_album_connections, find_connections_between  # noqa: E402
from app.graph.analysis import get_collection_stats, find_shared_personnel, get_hub_nodes  # noqa: E402
from app.services.research import nl_to_cypher, synthesize_query_response  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Query the Crate knowledge graph")
    parser.add_argument("question", nargs="?", help="Natural language question")
    parser.add_argument("--user-id", default="seed-user")
    parser.add_argument("--stats", action="store_true", help="Show collection stats")
    parser.add_argument("--collection", action="store_true", help="List collection")
    parser.add_argument("--shared", action="store_true", help="Find shared personnel")
    parser.add_argument("--hubs", action="store_true", help="Find hub nodes")
    parser.add_argument(
        "--connections", nargs=2, type=int, metavar=("ID1", "ID2"),
        help="Find connections between two albums (by Discogs ID)"
    )
    args = parser.parse_args()

    driver = get_neo4j_driver()

    try:
        if args.stats:
            with driver.session() as session:
                stats = session.execute_read(get_collection_stats, user_id=args.user_id)
            print(json.dumps(stats, indent=2))

        elif args.collection:
            with driver.session() as session:
                albums = session.execute_read(get_user_collection, user_id=args.user_id)
            for a in albums:
                artists = ", ".join(a["artists"][:3])
                print(f"  {a['year'] or '?'} | {a['title']} — {artists}")

        elif args.shared:
            with driver.session() as session:
                shared = session.execute_read(find_shared_personnel, user_id=args.user_id)
            for s in shared:
                print(f"  {s['artist']} appears on {s['album_count']} albums: {', '.join(s['albums'])}")

        elif args.hubs:
            with driver.session() as session:
                hubs = session.execute_read(get_hub_nodes, label="Artist", limit=15)
            for h in hubs:
                print(f"  {h['name']}: {h['connections']} connections")

        elif args.connections:
            with driver.session() as session:
                paths = session.execute_read(
                    find_connections_between,
                    album_id_1=args.connections[0],
                    album_id_2=args.connections[1],
                )
            if paths:
                for path in paths:
                    print("Path:")
                    for node in path["nodes"]:
                        labels = ", ".join(node["labels"])
                        name = node["props"].get("name") or node["props"].get("title", "?")
                        print(f"  ({labels}) {name}")
            else:
                print("No path found between these albums.")

        elif args.question:
            # Natural language query pipeline
            print(f"Question: {args.question}\n")

            # Generate Cypher
            cypher = nl_to_cypher(args.question)
            print(f"Generated Cypher:\n{cypher}\n")

            # Execute
            with driver.session() as session:
                result = session.run(cypher, user_id=args.user_id)
                records = [record.data() for record in result]

            if not records:
                print("No results found.")
                return

            # Synthesize response
            response = synthesize_query_response(
                args.question, json.dumps(records, indent=2, default=str)
            )
            print(response)

        else:
            parser.print_help()

    finally:
        close_neo4j_driver()


if __name__ == "__main__":
    main()
