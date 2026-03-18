# Crate — Implementation Plan

## Tech Stack (Decided)

### Backend
- **Language:** Python 3.12+
- **Framework:** FastAPI (async, good for IO-heavy work with external APIs)
- **Task queue:** Celery + Redis (Smart Add research is async — user shouldn't wait for 5 API calls)
- **Auth:** JWT tokens, simple email/password + invite codes for groups

### Databases
- **Neo4j** (Community Edition) — the knowledge graph. All music entities, relationships, and collection ownership. Cypher query language, which LLMs can generate.
- **PostgreSQL** — relational data: user accounts, groups, memberships, sessions, annotations, store reviews, feed events, want lists. Things that don't belong in the graph.
- **Redis** — caching, task queue broker, session store

### AI Layer
- **Claude API** (claude-sonnet-4-6) — primary LLM for:
  - Smart Add research synthesis (combining data from multiple sources into structured graph entities)
  - Natural language → Cypher query translation
  - Insight generation (narrative insights, connection stories, scene descriptions)
  - Entity extraction from unstructured text (forum posts, liner notes, Wikipedia articles)
- **Web search tool** — for Smart Add deep research (Tavily, Brave Search API, or SerpAPI)
- **Embeddings** — for semantic search across the graph (e.g., `text-embedding-3-small` or similar, stored in pgvector extension on PostgreSQL)

### External Data APIs
| API | Purpose | Auth | Rate Limits |
|---|---|---|---|
| **Discogs API** | Collection import, release metadata, credits, labels, market data | OAuth 1.0a | 60 req/min (auth'd) |
| **MusicBrainz API** | Detailed credits, recordings, relationships, artist metadata | None (User-Agent required) | 1 req/sec |
| **Spotify Web API** | Audio features (tempo, energy, key), album art, track previews | OAuth 2.0 | Varies |
| **Wikipedia/Wikidata API** | Cultural context, artist bios, historical events, city/scene info | None | Polite usage |
| **Musicbrainz Cover Art Archive** | Album artwork | None | 1 req/sec |

### Frontend
- **Framework:** Next.js 14+ (React, SSR, API routes)
- **Graph visualization:** `react-force-graph-3d` or `cytoscape.js` (interactive, zoomable graph explorer)
- **Sound Map:** Mapbox GL JS (geographic visualization, custom layers, smooth zoom/pan)
- **Charting:** D3.js for custom visualizations (timelines, influence flows, cluster diagrams)
- **UI components:** shadcn/ui + Tailwind CSS
- **State:** Zustand (lightweight, fits the app's needs)

### Infrastructure (Development → Production)
- **Dev:** Docker Compose (Neo4j, PostgreSQL, Redis, API, frontend — all local)
- **Prod (later):** Neo4j Aura Free → Aura Pro, PostgreSQL on Supabase or Railway, API on Fly.io or Railway, frontend on Vercel

---

## Project Structure

```
crate/
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── pyproject.toml              # uv/poetry, dependencies
│   ├── alembic/                    # PostgreSQL migrations
│   │   └── versions/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── config.py               # Settings, env vars
│   │   ├── dependencies.py         # Dependency injection (db sessions, auth)
│   │   │
│   │   ├── models/                 # SQLAlchemy models (PostgreSQL)
│   │   │   ├── user.py
│   │   │   ├── group.py
│   │   │   ├── annotation.py
│   │   │   ├── store.py
│   │   │   ├── feed_event.py
│   │   │   └── want_list.py
│   │   │
│   │   ├── graph/                  # Neo4j graph layer
│   │   │   ├── connection.py       # Neo4j driver setup
│   │   │   ├── schema.py           # Node/edge type definitions, constraints, indexes
│   │   │   ├── queries.py          # Core Cypher query builders
│   │   │   ├── ingestion.py        # Structured data → graph nodes/edges
│   │   │   └── analysis.py         # Graph algorithms (shortest path, hubs, clusters, etc.)
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── smart_add.py        # Orchestrates the Smart Add pipeline
│   │   │   ├── discogs.py          # Discogs API client
│   │   │   ├── musicbrainz.py      # MusicBrainz API client
│   │   │   ├── spotify.py          # Spotify API client
│   │   │   ├── wikipedia.py        # Wikipedia/Wikidata client
│   │   │   ├── research.py         # AI-powered web research (search + synthesis)
│   │   │   ├── insights.py         # Insight generation (individual + group)
│   │   │   ├── nl_query.py         # Natural language → Cypher → response
│   │   │   ├── collection.py       # Collection management (CRUD, import, ownership)
│   │   │   ├── group.py            # Group management (create, invite, merge graphs)
│   │   │   └── feed.py             # Feed event creation and retrieval
│   │   │
│   │   ├── tasks/                  # Celery async tasks
│   │   │   ├── smart_add_task.py   # Background research pipeline
│   │   │   ├── insights_task.py    # Periodic insight generation
│   │   │   └── pattern_task.py     # Pattern discovery scans
│   │   │
│   │   ├── api/                    # FastAPI routers
│   │   │   ├── auth.py
│   │   │   ├── collection.py
│   │   │   ├── graph.py
│   │   │   ├── query.py
│   │   │   ├── insights.py
│   │   │   ├── groups.py
│   │   │   ├── feed.py
│   │   │   ├── stores.py
│   │   │   └── annotations.py
│   │   │
│   │   └── prompts/                # LLM prompt templates
│   │       ├── smart_add.py        # Research synthesis prompts
│   │       ├── nl_to_cypher.py     # NL → Cypher translation
│   │       ├── insights.py         # Narrative insight generation
│   │       └── scene_context.py    # Scene/era/cultural context generation
│   │
│   └── tests/
│       ├── test_graph/
│       ├── test_services/
│       └── test_api/
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── app/                    # Next.js app router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Home / collection overview
│   │   │   ├── add/                # Smart Add flow
│   │   │   ├── graph/              # Graph explorer
│   │   │   ├── map/                # Sound Map
│   │   │   ├── feed/               # Group feed
│   │   │   ├── insights/           # Insights dashboard
│   │   │   ├── stores/             # Store map
│   │   │   ├── record/[id]/        # Single record deep dive
│   │   │   └── group/              # Group management & cross-collection views
│   │   │
│   │   ├── components/
│   │   │   ├── graph/              # Graph visualization components
│   │   │   ├── map/                # Mapbox components
│   │   │   ├── collection/         # Collection list, grid, cards
│   │   │   ├── insights/           # Insight cards, narratives
│   │   │   └── ui/                 # Shared UI (shadcn)
│   │   │
│   │   └── lib/
│   │       ├── api.ts              # API client
│   │       ├── store.ts            # Zustand stores
│   │       └── types.ts            # TypeScript types
│   │
│   └── public/
│
└── scripts/
    ├── seed_graph.py               # Dev seed data
    └── import_discogs.py           # CLI discogs import tool
```

---

## Graph Schema (Neo4j)

### Node Types

```cypher
// Core music entities
(:Album {discogs_id, musicbrainz_id, title, year, country, format, notes, cover_url})
(:Track {title, position, duration})
(:Artist {name, discogs_id, musicbrainz_id, bio, birth_year, death_year, origin_city})
(:Label {name, discogs_id, parent_label, founded_year, country})
(:Studio {name, city, country, lat, lng, active_years})
(:Genre {name})
(:Scene {name, city, country, era_start, era_end, description})
(:City {name, country, lat, lng})
(:Instrument {name})

// Collection/ownership
(:User {id, email, name})
(:Group {id, name, invite_code})
(:Pressing {discogs_id, country, year, plant, matrix_number, format_detail})

// Store map
(:Store {name, city, country, lat, lng, specialties, price_range, url})
```

### Edge Types

```cypher
// Music relationships
(:Artist)-[:PERFORMED_ON {instrument, role, tracks}]->(:Album)
(:Artist)-[:PRODUCED]->(:Album)
(:Artist)-[:ENGINEERED]->(:Album)
(:Artist)-[:WROTE {tracks}]->(:Album)
(:Album)-[:RELEASED_ON]->(:Label)
(:Album)-[:RECORDED_AT]->(:Studio)
(:Album)-[:HAS_TRACK {position}]->(:Track)
(:Album)-[:HAS_GENRE]->(:Genre)
(:Album)-[:PART_OF_SCENE]->(:Scene)
(:Album)-[:HAS_PRESSING]->(:Pressing)
(:Artist)-[:MEMBER_OF]->(:Artist)  // band membership
(:Artist)-[:INFLUENCED_BY]->(:Artist)
(:Label)-[:SUBLABEL_OF]->(:Label)
(:Scene)-[:LOCATED_IN]->(:City)
(:Studio)-[:LOCATED_IN]->(:City)
(:Artist)-[:FROM]->(:City)
(:Artist)-[:PLAYS]->(:Instrument)

// Collection ownership
(:User)-[:OWNS {date_added, purchase_location, purchase_price, notes, condition}]->(:Pressing)
(:User)-[:MEMBER_OF_GROUP {role, joined_at}]->(:Group)
(:User)-[:WANTS]->(:Album)

// Store map
(:User)-[:VISITED {date, found_records, notes, rating}]->(:Store)
(:Store)-[:LOCATED_IN]->(:City)
```

### Indexes & Constraints

```cypher
CREATE CONSTRAINT FOR (a:Album) REQUIRE a.discogs_id IS UNIQUE;
CREATE CONSTRAINT FOR (a:Artist) REQUIRE a.musicbrainz_id IS UNIQUE;
CREATE CONSTRAINT FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE INDEX FOR (a:Album) ON (a.title);
CREATE INDEX FOR (a:Artist) ON (a.name);
CREATE INDEX FOR (l:Label) ON (a.name);
CREATE INDEX FOR (s:Scene) ON (s.name, s.city);
CREATE FULLTEXT INDEX album_search FOR (a:Album) ON EACH [a.title];
CREATE FULLTEXT INDEX artist_search FOR (a:Artist) ON EACH [a.name];
```

---

## Smart Add Pipeline (Core Flow)

This is the most important flow in the app. When a user adds a record:

```
1. USER INPUT
   └── User provides: artist + title (or Discogs URL, or barcode scan)

2. IDENTIFY (fast, synchronous)
   ├── Search Discogs API → get release ID, basic metadata
   ├── Search MusicBrainz → get recording ID, cross-reference
   └── Return basic info to user for confirmation: "Is this the right release?"

3. DEEP RESEARCH (async, Celery task)
   ├── Discogs: full credits, tracklist, labels, formats, market data
   ├── MusicBrainz: detailed artist-recording relationships, session musicians per track
   ├── Spotify: audio features (tempo, energy, key, danceability) if available
   ├── Wikipedia: artist bios, label history, scene context
   ├── Web search (via AI): cultural context, recording stories, scene info
   │   └── AI synthesizes all sources into structured data:
   │       - Complete personnel list with instruments per track
   │       - Studio, engineer, producer identification
   │       - Scene/movement classification
   │       - Historical context paragraph
   │       - Notable anecdotes
   └── AI identifies which entities already exist in the graph (deduplication)

4. REVIEW (user interaction)
   └── Present enriched data to user:
       "Here's what I found. 8 musicians, recorded at X studio, part of Y scene.
        3 of these musicians already appear in your graph. Confirm or edit?"

5. INGEST (after confirmation)
   ├── Create/update nodes: Album, Artists, Label, Studio, Tracks, Scene, etc.
   ├── Create edges: PERFORMED_ON, PRODUCED, RELEASED_ON, RECORDED_AT, etc.
   ├── Create OWNS edge from user to pressing
   ├── Generate "Ripple" — what new connections this record created
   ├── Generate "Did you know?" insights triggered by this addition
   └── Create feed event for group members

6. NOTIFY GROUP
   └── Feed event: "Lucas added [Album]. This connects to [X] in Maria's collection."
```

---

## NL Query Pipeline

```
1. User asks: "What connects my Brazilian records to my jazz records?"

2. INTENT CLASSIFICATION (Claude)
   └── Classify: graph_query | insight_request | factual_question | session_request

3. CYPHER GENERATION (Claude)
   └── Generate Cypher query based on user's collection scope:
       MATCH (u:User {id: $user_id})-[:OWNS]->(:Pressing)<-[:HAS_PRESSING]-(a:Album)
       WHERE ... (Brazilian + jazz intersection logic)

4. EXECUTE against Neo4j

5. RESPONSE SYNTHESIS (Claude)
   └── Take raw graph results, generate narrative response:
       "Your Brazilian and jazz collections connect through 3 musicians..."
```

---

## Development Phases

### Phase 1: Foundation (Weeks 1–3)
**Goal:** A working pipeline where you add one record and it builds a rich graph node.

**Deliverables:**
- Docker Compose setup (Neo4j, PostgreSQL, Redis, FastAPI)
- Neo4j schema: all node types, edge types, constraints, indexes
- PostgreSQL models: User (basic, no auth yet — single-user mode)
- Discogs API client: search releases, get full release data
- MusicBrainz API client: get recording relationships, artist credits per track
- Smart Add pipeline (steps 1-5, synchronous first, no Celery yet):
  - Input: artist + title
  - Output: complete graph node with all relationships
- AI research synthesis: Claude takes raw API data → structured graph entities
- Graph ingestion: structured entities → Neo4j nodes and edges
- Basic CLI tool: `python scripts/add_record.py "Miles Davis" "Kind of Blue"` → see graph populated
- Seed script: add 10-20 records to have a working graph to query against

**Tech tasks:**
- [ ] Set up monorepo, Docker Compose, `.env` configuration
- [ ] Neo4j driver setup, schema creation script
- [ ] PostgreSQL + Alembic setup, User model
- [ ] Discogs API client with OAuth
- [ ] MusicBrainz API client with rate limiting
- [ ] Claude integration for entity extraction and synthesis
- [ ] Graph ingestion module (structured data → Cypher)
- [ ] Smart Add orchestrator (ties it all together)
- [ ] CLI add tool + seed script
- [ ] Basic tests for each component

### Phase 2: Individual Core (Weeks 4–6)
**Goal:** A single user can import their collection, explore the graph, and ask questions.

**Deliverables:**
- Discogs collection import (bulk — iterate user's Discogs collection, run Smart Add for each)
- Celery + Redis for async Smart Add (import can run in background)
- NL query pipeline: natural language → Cypher → narrative response
- Basic REST API:
  - `POST /collection/add` — Smart Add
  - `POST /collection/import/discogs` — bulk import
  - `GET /collection` — list user's records
  - `POST /query` — natural language query
  - `GET /graph/record/{id}` — single record with all connections
  - `GET /graph/explore` — neighborhood query (start from a node, expand)
- Basic insights on add: "Did you know?" triggered when a record connects to existing graph
- Frontend v0 (minimal):
  - Collection list view
  - Smart Add form (search → confirm → watch it populate)
  - Record detail page (all connections, context, credits)
  - Simple graph explorer (click a node, see connections, expand)
  - NL query input + response display

**Tech tasks:**
- [ ] Celery setup, Smart Add as async task with status tracking
- [ ] Discogs bulk import (paginated, respecting rate limits)
- [ ] NL → Cypher pipeline with Claude
- [ ] REST API (FastAPI routers)
- [ ] "Did you know?" insight generator (runs on each add)
- [ ] Next.js project setup, shadcn/ui, API client
- [ ] Collection list + Smart Add UI
- [ ] Record detail page
- [ ] Graph explorer with `react-force-graph` or `cytoscape.js`
- [ ] NL query interface

### Phase 3: Group Layer (Weeks 7–10)
**Goal:** Multiple users, groups, cross-collection graph, and the feed.

**Deliverables:**
- Auth: JWT, email/password registration, login
- Group model: create group, generate invite code, join via code
- Cross-collection graph queries: query across all members' collections
- The Feed:
  - Feed events generated on Smart Add (new record, new connections)
  - Chronological feed per group
  - AI-enriched context on each event ("Lucas added X. This connects to Y in Pedro's collection.")
- Collaborative annotations: any group member can annotate any node
- Group insights v1:
  - Collection overlap / divergence between members
  - "The Bridge" — who connects different areas of the group graph
  - Collective blind spots
- Cross-collection NL queries: "What connects Pedro's collection to mine?"
- Frontend:
  - Auth pages (login, register)
  - Group creation / join flow
  - Feed page
  - Group graph view (color-coded by owner)
  - Annotation UI on nodes

**Tech tasks:**
- [ ] JWT auth middleware, user registration/login API
- [ ] Group model, invite code generation, membership API
- [ ] Feed event model + generation on Smart Add
- [ ] Feed API (paginated, per group)
- [ ] AI context generation for feed events
- [ ] Annotation model + API
- [ ] Cross-collection Cypher queries (filter by group membership)
- [ ] Group insight generator (overlap, bridges, blind spots)
- [ ] Auth UI (login, register, group management)
- [ ] Feed UI
- [ ] Group graph explorer (multi-user, color-coded)
- [ ] Annotation UI

### Phase 4: The Map & Insights (Weeks 11–14)
**Goal:** Sound Map, deep insights engine, and core creative features.

**Deliverables:**
- Sound Map:
  - Geographic visualization of collection (Mapbox)
  - Records plotted by origin city (not purchase location)
  - Density heatmap: dense = well-explored, empty = uncharted
  - Click a city → see all records, artists, labels, scenes from there
  - Group view: everyone's records on one map
- Uncharted Territory:
  - Graph analysis identifies scenes/regions the collection touches but doesn't cover deeply
  - AI generates descriptions of what's in the uncharted area
- Insights engine v2:
  - Collection DNA (auto-generated profile of taste)
  - Temporal insights (decade breakdown, "what was happening")
  - Narrative connection stories
  - Rarity/value context from Discogs market data
- The Thread: pick two points, get the narrative connecting them
- The Ripple v2: richer visualization of what a new record connects to
- Store Map v1:
  - Add stores with location, specialties, notes
  - Map visualization (Mapbox, separate layer)
  - Group members' reviews and visit history

**Tech tasks:**
- [ ] City geocoding pipeline (ensure all City nodes have lat/lng)
- [ ] Mapbox integration in frontend
- [ ] Sound Map component (point layer, heatmap layer, click interactions)
- [ ] Uncharted Territory algorithm (edge detection on graph clusters)
- [ ] AI narrative generation for uncharted areas
- [ ] Collection DNA generator (graph analysis → AI narrative)
- [ ] Temporal insights (decade grouping, AI context)
- [ ] The Thread: shortest path + AI narrative synthesis
- [ ] The Ripple: new-record impact visualization
- [ ] Store model (PostgreSQL), Store API (CRUD, reviews)
- [ ] Store Map frontend (Mapbox layer)
- [ ] Spotify API integration (audio features for listening sessions)
- [ ] Listening session generator v1

### Phase 5: AI Music Historian (Weeks 15–18)
**Goal:** Pattern discovery, invisible networks, migration mapping, and group rituals.

**Deliverables:**
- Invisible Networks:
  - Hub detection algorithm (betweenness centrality, degree centrality in Neo4j)
  - AI-generated profiles for top unsung nodes
  - "Hall of fame for the unsung" view
- Pattern Discovery:
  - Periodic Celery task scans group graph for patterns
  - Pattern types: instrument clusters, temporal hotspots, cross-genre bridges, geographic echoes, convergence
  - AI generates explanations for discovered patterns
  - Patterns delivered via feed or dedicated insights page
- Migration Mapping:
  - Track artist/genre movement across cities over time
  - Animated flow visualization on Sound Map (D3 + Mapbox)
  - AI-generated narrative for each migration path
- Scene Explorer:
  - Pick city + era → AI builds cultural picture from graph + world knowledge
  - Shows what you own from that scene, what's adjacent
- Group Rituals:
  - The Rotation: monthly pick flow, AI briefing generation
  - Dig Challenge: system identifies white spaces, proposes challenges
  - Crate Census: yearly stats aggregation + AI narrative summary
- Who Built This Scene: infrastructure analysis for any graph cluster
- Era Deep Dive: decade narrative generation

**Tech tasks:**
- [ ] Neo4j graph algorithms (GDS library): centrality, community detection, pathfinding
- [ ] Invisible Networks pipeline (centrality → filter famous → AI profile generation)
- [ ] Pattern Discovery Celery task (scheduled, runs weekly or on threshold events)
- [ ] Pattern type detectors (temporal clustering, instrument co-occurrence, geographic analysis)
- [ ] AI pattern explanation generator
- [ ] Migration Mapping: temporal-geographic queries, D3 animated flow component
- [ ] Scene Explorer: AI context generation, graph subgraph extraction
- [ ] Rotation/challenge/census models and API
- [ ] Rotation UI: pick, notify, briefing display
- [ ] Dig Challenge UI: current challenge, white space visualization
- [ ] Census generator: yearly aggregation task

### Phase 6: Polish & Scale (Weeks 19–22)
**Goal:** Performance, mobile responsiveness, advanced features, deployment.

**Deliverables:**
- Performance optimization:
  - Neo4j query optimization (profiling, index tuning)
  - API response caching (Redis)
  - Frontend: lazy loading, virtualized lists, graph LOD (level of detail)
- Mobile responsiveness (not native, but usable on phone — important for dig scenarios)
- Discogs OAuth flow (user connects their Discogs account)
- Advanced NL queries (multi-hop, temporal, cross-collection)
- Influence Flows visualization (animated timeline of graph growth)
- The Collector's Perspective: AI-generated essay about group's music worldview
- Before and After: per-record historical context
- The Missing Link: disconnected subgraph analysis + bridge identification
- Want list coordination (group want lists, trip-aware notifications)
- Notifications (email or push — lightweight)
- Production deployment (Docker → cloud infrastructure)
- Monitoring, error tracking (Sentry), logging

---

## Key Dependencies

```
# Backend (Python)
fastapi
uvicorn
sqlalchemy[asyncio]
alembic
asyncpg                    # PostgreSQL async driver
neo4j                      # Official Neo4j Python driver
celery[redis]
anthropic                  # Claude API
httpx                      # Async HTTP client (for external APIs)
pydantic
python-jose[cryptography]  # JWT
passlib[bcrypt]            # Password hashing
python-musicbrainzngs      # MusicBrainz client
spotipy                    # Spotify client

# Frontend (Node.js)
next
react
typescript
tailwindcss
@shadcn/ui
zustand
react-force-graph          # Or cytoscape
mapbox-gl
react-map-gl
d3
swr                        # Data fetching
```

---

## External Accounts Required

| Service | What for | Free tier |
|---|---|---|
| **Discogs** | Developer app (API key + OAuth) | Yes, 60 req/min |
| **MusicBrainz** | Just needs User-Agent header | Fully free |
| **Spotify** | Developer app (client ID + secret) | Yes, rate limited |
| **Anthropic** | Claude API key | Pay per token |
| **Mapbox** | Map tiles + geocoding | 50k loads/month free |
| **Tavily or Brave Search** | Web search for AI research | Tavily: 1k searches/month free |

---

## Data Flow Summary

```
                    ┌─────────────┐
                    │   User adds  │
                    │   a record   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Identify   │  ← Discogs + MusicBrainz search
                    │   (sync)     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  User       │
                    │  confirms   │
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │     Deep Research       │  ← Celery async task
              │  (Discogs + MB +        │
              │   Spotify + Wikipedia   │
              │   + Web Search)         │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │    AI Synthesis         │  ← Claude: raw data → structured entities
              │  (entity extraction,    │
              │   deduplication,        │
              │   context generation)   │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │    Graph Ingestion      │  ← Neo4j: create nodes + edges
              └────────────┬────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
   ┌─────▼─────┐   ┌──────▼──────┐   ┌─────▼─────┐
   │  Insights  │   │  Feed Event │   │  Ripple   │
   │ "Did you   │   │ "Lucas      │   │ New       │
   │  know?"    │   │  added X"   │   │ connections│
   └───────────┘   └─────────────┘   └───────────┘
```
