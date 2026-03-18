# Crate — A Collectively-Built Map of Music History

**Pillar:** Fun
**Status:** Planned
**Started:** 2026-03-16

## What

Crate builds a knowledge graph of music — starting from your vinyl collection and growing through your friends'. Each record is a data point that anchors to a place, a time, a set of people, a cultural moment. As the group adds more records, the map fills in, and you start to see how music scenes formed, how genres migrated across continents, how collaboration shaped sound, and how society and music shaped each other.

**The vinyl collection is the entry point. What you're really building is a living map of how music shaped and was shaped by the world — one record at a time.**

## Core Philosophy

- **AI is the librarian, humans are the explorers** — AI enriches, researches, connects, and generates insights. Humans discover, share, and recommend to each other.
- **Discovery stays human** — no algorithmic recommendations. Finding music is physical and social — left to chance and curiosity, just like finding a record in a shop you've never been to.
- **Anti-algorithm** — expand the map, don't narrow it. Show connections, lineages, scenes, and rabbit holes. Let curiosity drive.
- **Individual is the building block, group is the product** — one person's graph has hidden connections. Five friends' graphs have stories. The combined graph becomes a collective knowledge base none of you could build alone.
- **Useful from day one with one person** — the group layer amplifies, but isn't required.

## Architecture: Three Layers

### Layer 1: Individual Experience (The Building Block)
Your personal graph. Add records, the AI deeply researches each one (musicians, studios, scenes, history), and builds a rich knowledge graph of your collection.

- **Smart Add** — add a vinyl, AI researches it across multiple sources (Discogs, MusicBrainz, AllMusic, Wikipedia, forums). Full session credits, recording details, cultural context, pressing info, anecdotes.
- **Knowledge Graph** — deep, accurate, richly connected. Artists, albums, tracks, labels, producers, engineers, session musicians, studios, genres, scenes, cities, pressings. Quality of edges > quantity of nodes.
- **Natural Language Queries** — ask anything about your collection. Blends collection data with world knowledge.
- **Insights Engine** — narrative insights, not just stats. Collection DNA, proactive "did you know?" moments, connection stories, temporal insights.
- **Listening Session Curation** — graph-informed session building. Sequence records by connections, not just genre.
- **Dig Assist** — gap analysis, trip briefings (context, not commands), want lists driven by graph.

### Layer 2: Group Experience (The Main Focus)
When individual graphs combine, you learn from the group. The collective graph becomes a living knowledge base built from lived experience.

- **Cross-Collection Graph** — merged view. Overlaps, gaps, each person's depth in different areas.
- **Group Insights** — crew DNA, taste distance, bridges between collections, collective blind spots, shared lineages, taste evolution over time.
- **The Feed** — chronological, human-driven. What friends are adding, with AI context. No algorithm.
- **Trip Reports & Dig Intelligence** — accumulated map of where the group has dug, shop intelligence, city briefings powered by friends' past finds.
- **Cross-Pollination** — visibility into friends' finds and how they connect to your graph. Not recommendations — just making knowledge accessible.
- **Collaborative Annotations** — anyone annotates any node. Human knowledge layered on AI research.
- **Group Coordination** — shared want lists, dig challenges, shared exploration themes.

### Layer 3: Creative & Exploratory Features
The graph enables deeper exploration of music as culture.

- **Vinyl Archaeology** — trace a record's lineage (influences, outcomes), reconstruct recording sessions.
- **Sound Map** — collection plotted geographically by where the music came from. Zoom into cities, see scenes and labels.
- **Scene Explorer** — pick a city + era, AI builds the cultural picture. Migration paths of genres across continents.
- **Group Rituals** — monthly rotation (one person picks, everyone listens), dig challenges, yearly crate census.
- **Record as Story Object** — personal + historical stories layered on every record. Collection as memoir.
- **Graph Analysis** — shortest path as research tool (revealing hidden intermediaries and scene structure), hub detection, cluster analysis, outlier detection, collection chains.

## The Bigger Picture

Each record is evidence of something larger:
- **How scenes formed** — who played with who, where, and what came out of it
- **How music migrated** — a genre born in Lagos, carried to London by specific musicians, transformed in NYC by specific producers
- **How collaboration shaped sound** — the same bassist on 15 records across 3 cities over a decade tells you how ideas traveled
- **How society shaped music** — political upheaval in Brazil → Tropicália, apartheid → South African jazz diaspora, post-war Japan → jazz kissaten culture
- **The invisible infrastructure** — the studios, engineers, labels, and producers that enabled scenes to exist

The knowledge graph isn't just about your records. It's about **what your records are evidence of**.

## The Motivation Loop

The graph has gaps — and those gaps are the motivation. Not "buy this record" but **"there's a story here and you're missing a chapter."**

- "You have 6 records from the Lagos funk scene but nothing from the Afrobeat side happening in the same city — there's a whole chapter missing"
- "Three of your records feature a bassist who played on 40+ sessions in 1970s Kingston. You're only seeing a fragment of that story."
- "Your group has deep MPB coverage but the entire Tropicália movement that preceded it is empty. That's the origin story."

Every record someone finds and adds expands the group's map. Pedro goes to Rio, finds a Tropicália record — suddenly a new region lights up and connects to 5 things Maria already owns. Digging becomes purposeful beyond personal collecting. You're not just buying records, you're **building a collective understanding of music history**.

## Tech Stack (Tentative)

- **Backend:** Python (FastAPI or similar)
- **Knowledge graph:** Neo4j or NetworkX for prototyping
- **Data sources:** Discogs API, MusicBrainz, Wikipedia, Spotify API (for audio features), AllMusic, web search
- **AI layer:** LLM for natural language queries, entity extraction, research, insight generation
- **Frontend:** Web app (could start as CLI/notebook for prototyping)
- **CV (optional):** Record cover/label scanning for collection input

## What This Is NOT

- Not a social network competing with Discogs
- Not a streaming service or playlist generator
- Not an algorithm telling you what to buy or listen to
- It's a tool for **understanding and exploring music history through the records you and your friends collect**
