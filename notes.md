# Crate — Brainstorm Notes

## Vision Statement

**A collectively-built map of music history — one record at a time.**

Crate builds a knowledge graph of music starting from your vinyl collection and growing through your friends'. Each record anchors to a place, a time, a set of people, a cultural moment. As the group adds records, the map fills in — revealing how scenes formed, how genres migrated, how collaboration shaped sound, and how music and society shaped each other.

The graph has gaps. Filling them is the motivation. Not because an algorithm told you to buy something, but because you can *see* the missing chapter in the story. "You have 6 records from the Lagos funk scene but nothing from the Afrobeat side happening in the same city at the same time — there's a whole chapter missing." That makes you want to go out and find it. Every record someone digs up and adds expands the group's understanding of music history. Digging becomes purposeful beyond personal collecting.

**Design principles:**
- **AI is the librarian, humans are the explorers** — AI enriches, researches, connects, and generates insights. Humans discover, share, and recommend to each other.
- **Discovery stays human** — no algorithmic recommendations. Sharing and recommending comes from people, not machines. Like finding a record in a shop — left to chance and curiosity.
- **The graph motivates exploration** — visible gaps in the map create natural curiosity. "There's a story here and you're missing a chapter" is more compelling than "you might like this."
- **Every record expands the map** — adding a record doesn't just grow your collection, it lights up new connections across the group graph. One Tropicália find in Rio might connect to 5 records Maria already owns.
- **Anti-algorithm** — expand the map, don't narrow it. Show connections and context, let curiosity drive.
- **Useful from day one with one person** — the group layer amplifies, but isn't required.

---

## Layer 1: Individual Experience (The Building Block)

### 1.1 Collection Input & Cataloging
- **Discogs import** — bulk-load existing collection via API
- **Manual entry** — search by artist/title, auto-pull metadata
- **Cover scan (stretch)** — photo of a record, CV narrows candidates
- **Barcode/matrix number scan** — identify specific pressings
- Metadata enrichment from Discogs, MusicBrainz, Spotify, Wikipedia

### 1.2 AI-Assisted Record Research ("Smart Add")
- When you add a vinyl, the AI **actively researches** it using web search and multiple data sources
- Goes beyond basic metadata:
  - Full session musician credits (who played what instrument on which track)
  - Recording details (studio, date, engineer)
  - Cultural/historical context (what scene, what was happening at the time)
  - Pressing details (country, plant, matrix info, originals vs reissues)
  - Anecdotes and stories (session stories, label drama, etc.)
- Present findings for user review before committing to graph
- Like having a record-nerd friend who instantly researches everything

### 1.3 Knowledge Graph (The Core — P0 Quality)
- **Node types:** Artist, Album, Track, Label, Producer, Engineer, Session Musician, Studio, Genre, Scene, City, Year, Pressing
- **Edge types:** "played on", "produced by", "released on", "recorded at", "part of scene", "influenced by", "same era", "same city"
- Quality of edges > quantity of nodes. "Herbie Hancock played Rhodes on track 3" > "jazz album"
- Multiple data sources, cross-referenced, AI-enriched
- Hidden connections:
  - Shared personnel across albums
  - Label family trees (sub-labels, reissue labels)
  - Studio clusters ("3 of your records were cut at Rudy Van Gelder's studio")
  - Scene mapping (who played with who in a city/era)
- **Graph exploration UI** — interactive, zoomable, filterable
- **"Why is this interesting?"** — AI-generated context for every connection

### 1.4 Natural Language Queries
- "What do I have from the Blue Note 1500 series?"
- "Show me all the records where Herbie Hancock plays but isn't the leader"
- "What connects my Brazilian records to my jazz records?"
- "Which of my records were pressed in Japan?"
- "Give me the story of how Detroit techno connects to Kraftwerk through my collection"
- Queries that blend collection data with world knowledge

### 1.5 Insights Engine
- **Collection DNA** — what defines your taste, auto-generated from graph analysis
- **"Did you know?"** — proactive insights when you add a record
  - "This is the 5th record featuring Ron Carter on bass"
  - "You now own 3 CTI Records albums — here's what that label was about"
- **Narrative insights** — the AI tells stories, not just stats
  - "Here's how your collection traces the evolution of Afrobeat from Lagos to London"
  - "Your collection is heaviest in 1969-1974. Here's what was happening in music then."
- **Rarity & value alerts** — "This pressing is uncommon, only X listed on Discogs"

### 1.6 Listening Session Curation
- "Friends coming over, pick 5 funk records for tonight"
- "Give me a 2-hour journey through my collection that tells a story"
- "What should I play for someone who's never listened to jazz?"
- Graph-informed sequencing: connect records by shared musicians, producers, labels
- Themed sessions: "all from 1972", "a tour of Lagos through music", "records featuring flute"
- Flow awareness: energy, tempo, mood progression (Spotify audio features)

### 1.7 Dig Assist
- **Gap analysis** — "You have 7 of 10 essential Fela Kuti albums — here are the 3 missing"
- **Trip prep** — context about a city's music scenes, labels, history (not "buy this" — just a briefing)
- **Want list generation** — driven by graph connections, not algorithmic taste-matching
- **Price context** — typical value, pressing variations

---

## Layer 2: The Group Experience (The Main Focus)

The individual graph is the building block. When combined with others, you learn from the group. The group graph becomes a collective knowledge base none of you could build alone.

### 2.1 Cross-Collection Graph
- Merge individual graphs into a shared, queryable view
- See overlaps: "4 of you own this album"
- See gaps: "Nobody in the group has anything from this label"
- Each person brings depth in different areas — Pedro knows Brazilian music, Maria knows Detroit, you know Japanese jazz. Combined = a deep, wide music encyclopedia.
- **Human-verified data** — this isn't Discogs or Wikipedia. It's knowledge from people who own and listen to these records.

### 2.2 Group Insights (AI-Powered)
- **The Crew's DNA** — what defines the group's collective taste? Where do you converge, where do you diverge?
- **"The Bridge"** — "João is the only one connecting the Afrobeat side to the electronic side. His collection is the bridge."
- **Collective blind spots** — "Nobody owns anything from the Ethiopian jazz scene, despite adjacent records"
- **Taste distance** — how similar or different are two members' collections? Conversation starters, not competition.
- **Group timeline** — combined collection mapped across decades. Where does the group go deep?
- **Shared lineages** — "3 of you independently collected records from the same obscure Detroit scene"
- **Group taste evolution** — how has the collective taste shifted over time? Who's exploring new territory?

### 2.3 The Feed (Human-Driven Sharing)
- Simple chronological feed of what everyone's adding — not algorithmic
- "Pedro added X yesterday" with AI-generated context for why it's interesting
- The AI enriches, but **discovery and sharing are fully human**
- You see a friend's find, you get curious, you ask them about it — the conversation happens between people

### 2.4 Trip Reports & Dig Intelligence
- **Who's been where** — aggregated map of where the group has dug. Over years, this becomes serious intelligence.
- **City briefings powered by the group** — "Going to São Paulo? Here's what Pedro found there last year, plus scenes and labels connected to your collection"
- **Shop intelligence over time** — "This shop in Lisbon has yielded 12 finds across the group, mostly Portuguese funk and African records"
- **Trip reports** — add records from a trip, system generates a summary: "Lucas added 8 records in Tokyo. 3 new artists entered the group graph. 2 connect to Maria's collection."

### 2.5 Cross-Pollination
- **Visibility, not recommendations** — "Pedro added 4 records from a label you've never encountered. Here's what that label is about and how it connects to things you own."
- **"If you could borrow 5 records from the group, which would add the most to your graph?"** — graph analysis, not taste-matching
- **Learning from each other** — the combined graph teaches you about music you didn't know existed, through people you trust

### 2.6 Collaborative Annotations
- Anyone in the group can annotate any node in the shared graph
- "I saw this band live in '98, the drummer is insane"
- "Don't buy this pressing, the mastering is flat"
- Human knowledge layered on top of AI research — this is what makes it a living knowledge base

### 2.7 Group Dig Coordination
- "I'm going to Lisbon next month — does anyone need me to look for something?"
- Group want lists: the system knows what everyone's hunting for
- Shared exploration themes: "we're all exploring Ethiopian jazz this month"
- No algorithm, just a shared mission with AI providing background research

### 2.8 Group Listening Sessions
- "Build a session from records we collectively own"
- "Create a listening journey that touches at least one record from each person's collection"
- Session curation across collections, connected by the graph

---

## Layer 3: Creative & Exploratory Features

### 3.1 Vinyl Archaeology
- **"The Lineage"** — pick any record, AI traces its musical DNA backwards and forwards. Who influenced it? What did it influence? Where did the musicians go after?
- **"The Session"** — reconstruct the recording session. Who was in the room, what studio, what year, what else was happening in that city musically. A documentary snapshot.

### 3.2 Geographic / Cultural Layer
- **"Sound Map"** — collection plotted on a world map by where the music *came from* (Lagos, Detroit, Tokyo, Kingston). Zoom into a city, see the scenes, labels, studios.
- **"Scene Explorer"** — pick a city + era, AI builds the picture: who was playing, what labels, which studios, what was in the air. Shows what you own from that scene.
- **"Migration Paths"** — how did genres travel? Trace Afrobeat from Lagos to London to NYC through records in the group's collection.

### 3.3 Time-Based Features
- **"This Week in Vinyl History"** — weekly, AI picks something from the group's collection with an anniversary. "45 years ago this week, this album was recorded in a single session in Rio."
- **"Seasonal Curation"** — mood-aware listening suggestions from your collection. Subtle, not pushy.

### 3.4 Group Rituals
- **"The Rotation"** — each month, one person picks a record, everyone listens. AI generates a deep briefing. Low-effort ritual that keeps the crew connected.
- **"Dig Challenge"** — "this month, find something from a label nobody in the group owns." The group graph identifies the white spaces.
- **"Crate Census"** — yearly group summary. "In 2026 we added 200 records, visited 15 cities, discovered 30 new artists. Pedro found the rarest pressing. Maria expanded the map into Ethiopian music."

### 3.5 The Record as a Story Object
- **"The Story Behind"** — every record has a personal story (where you found it, what it means) and a historical story (the session, the era, the label). Layer both. Collection becomes a memoir.
- **"Conversation Starter"** — at someone's house, scan a record you don't know. Instantly get context + connections to your own collection. "You don't own this, but the bassist is on 4 records you have."

### 3.6 Graph Analysis / Data Engineering
- **Shortest path analysis** — "How does my Fela Kuti connect to my Herbie Hancock?" The path reveals real musical lineage (e.g., Tony Allen → Afrobeat drumming → jazz-funk crossover → Headhunters)
  - The nodes *in between* are often the most interesting — hidden intermediaries (a session musician, a studio, a label that bridges two worlds)
  - Cross-collection: "How does Pedro's Brazilian collection connect to Maria's Detroit records?" — reveals shared lineages neither knew about
  - Run shortest paths between multiple records from the same era/city → reveals the **structure of a scene** (which people and places were the hubs)
- **Collection coherence** — if most records connect in 2-3 hops, your collection has strong internal logic. 8 hops away = your outlier.
- **"How did I get here?"** — trace the path from your first record to your latest addition. The path tells the story of how your taste evolved.
- **Hub detection** — which artists, labels, or studios are the most connected nodes in your graph? These are the pillars of your collection.
- **Cluster analysis** — automatically detect "neighborhoods" in your collection. Maybe you didn't realize you have three distinct clusters: 70s jazz, 90s electronic, and Brazilian MPB.
- **"The Outlier"** — which record is most disconnected from everything else? That's probably the most interesting one.
- **"Collection chain"** — what's the longest unbroken chain of connections? Record A shares a musician with B, B shares a label with C, C recorded at the same studio as D...

### 3.7 AI as Music Historian (Invisible Networks, Pattern Discovery, Migration Mapping)

These features use graph analysis + AI to reveal things that aren't in any book or article. They emerge purely from the collective data.

**Invisible Networks**
- Rank nodes by connectivity — the most connected person in the group graph might be someone nobody can name
- AI generates profiles for the unsung: "This person played on X records in your collection across Y years in Z cities. Here's their story."
- Over time, the group builds a **hall of fame for the unsung** — session players, engineers, producers who shaped the sound but never got the headline
- Also surfaces invisible *places* — a studio that appears on 20 records, an engineer who mixed half a scene
- Example: "Rudy Van Gelder's studio appears on 14 records across 3 collections. He wasn't a musician, but his room *is* the Blue Note sound."

**Pattern Discovery**
- AI periodically scans the group graph for emergent patterns nobody asked about
- Types of patterns:
  - **Instrument-based:** "12 records across 4 collections prominently feature the Rhodes piano. Here's the thread."
  - **Temporal clusters:** "Something happened in 1974 — the group owns more records from that year than any other. Here's what was going on."
  - **Cross-genre bridges:** "Your funk and electronic collections share 3 producers. That's not a coincidence — here's the story of how funk became electronic."
  - **Geographic echoes:** "Records from Lagos and New Orleans share rhythmic DNA. Here's the West African root."
  - **Convergence:** "3 of you independently collected records from the same obscure scene without knowing it."
- The key: **the AI finds it, then explains why it matters.** Not just "here's a pattern" but "here's what this tells you about music history."

**Migration Mapping**
- Track how people, sounds, and ideas moved geographically through the graph
- **People:** "This saxophonist went Lagos → London → NYC. Each city changed his playing. Here's how, album by album, through records in your group's collection."
- **Sounds:** "The drum break on this record ended up in hip-hop via sampling, but the drumming style itself traces back to New Orleans second line. Your collection has both endpoints."
- **Ideas:** "The concept of dub — stripping a track and rebuilding it — started in Kingston, moved to London via immigration, became the foundation of electronic music in Berlin. Your group owns records from every stop."
- Visualize as animated flows on the Sound Map — watch ideas travel across continents and decades
- Each migration path is a **story the AI tells**, anchored by records the group actually owns

---

## Final Feature Set (2026-03-17)

### Core — Serves the vision directly
| Feature | What it does |
|---|---|
| **Smart Add + AI Research** | Add a vinyl, AI researches it deeply (musicians, studios, scenes, history, pressing info) across multiple sources |
| **Knowledge Graph** | Deep, accurate, richly connected graph. Quality of edges > quantity of nodes. P0. |
| **The Map** | Visual, geographic, explorable map of music history built from your collection. Dense = known, empty = unexplored. Grows with every record added. |
| **Uncharted Territory** | Identifies edges of your map — scenes/eras/regions your collection touches but doesn't fully cover. "There's an iceberg under that one record." |
| **The Thread** | Pick any two points, AI weaves the historical narrative connecting them using your records as evidence |
| **The Ripple** | Add a record, see how it connects to a movement that changed music. Makes every addition feel significant. |
| **The Missing Link** | What records would bridge disconnected parts of your map? Not a recommendation — a research finding. |
| **Cross-Collection Graph** | Merged group graph. Overlaps, gaps, each person's depth in different areas. |
| **Group Insights** | Crew DNA, taste distance, bridges, blind spots, shared lineages, taste evolution |
| **Store Map** | Collaborative map of record shops, fairs, flea markets, sellers. Tagged with specialties, price range, vibes. Reviews and tips from the group. Accumulated dig intelligence over time — "this shop in Lisbon has yielded 12 finds across the group." |

### Enrichment — Makes each record and the graph deeper
| Feature | What it does |
|---|---|
| **Who Built This Scene** | The infrastructure behind the music — session musicians, engineers, label owners, studios |
| **Before and After** | What was the landscape before this record, how did it change after? |
| **Era Deep Dive** | A decade narrated through your collection |
| **The Collector's Perspective** | AI essay about your group's view of music history, updated as the collection grows |
| **Influence Flows** | Animated visualization of how ideas moved through your graph over time |
| **The Lineage** | Trace a record's musical DNA backwards and forwards |
| **The Session** | Reconstruct the recording session — who was in the room, documentary snapshot |

### AI as Music Historian — Original analysis from collective data
| Feature | What it does |
|---|---|
| **Invisible Networks** | Surface the most connected but least famous nodes — the session musicians, engineers, studios that shaped the sound without getting the headline. "Hall of fame for the unsung." |
| **Pattern Discovery** | AI scans the group graph for emergent patterns: instrument clusters, temporal hotspots, cross-genre bridges, geographic echoes, independent convergence. Finds it, then explains why it matters. |
| **Migration Mapping** | Track how people, sounds, and ideas moved geographically — visualized as animated flows on the Sound Map. Each migration is a story anchored by records the group owns. |

### Social — Human-driven, AI-enriched
| Feature | What it does |
|---|---|
| **The Feed** | Chronological, no algorithm. What friends are adding, with AI context. |
| **Trip Reports** | Add records from a trip, system summarizes what changed in the group graph |
| **Dig Intelligence** | Accumulated map of where the group has dug. City briefings powered by friends' past finds. |
| **Collaborative Annotations** | Anyone annotates any node. Human knowledge on top of AI research. |
| **The Rotation** | Monthly: one person picks a record, everyone listens. AI generates a deep briefing. |
| **Dig Challenge** | "Find something from a label nobody owns." Group graph identifies white spaces. |
| **Crate Census** | Yearly group summary — records added, cities visited, new artists discovered, milestones. |

### Utility
| Feature | What it does |
|---|---|
| **NL Queries** | Ask anything about your collection, blending collection data with world knowledge |
| **Insights Engine** | Narrative insights, collection DNA, proactive "did you know?" moments |
| **Listening Sessions** | Graph-informed curation across individual or group collections |
| **Dig Assist** | Gap analysis, trip prep, want lists driven by graph |
| **Graph Analysis** | Shortest path, hub detection, cluster analysis, outliers, collection coherence, collection chains |

### Secondary (Park for Later)
- Audio integration (Spotify/Tidal links, playlists)
- Condition & grading tracker
- Trading / marketplace (lightweight)
- Wax archaeology (matrix decoder, pressing plant ID)
- Collection journaling (acquisition log, anniversary reminders)

---

## MVP Candidates

1. **Smart Add flow** — add one record, AI researches it deeply, builds rich graph node → proves the core magic
2. **Discogs import → Graph → Simple query interface** — proves scale value
3. **"What connects these two records?"** — a single compelling interaction
4. **CLI/notebook prototype** — skip frontend, just graph + natural language

---

## Open Questions
- Neo4j vs. lighter alternatives (NetworkX, SQLite with graph extensions, SurrealDB)?
- How much to lean on LLM world knowledge vs. structured data from APIs?
- Mobile-first or web-first?
- How to handle records not in Discogs (white labels, bootlegs, local pressings)?
- Privacy: collection data is personal — self-hosted? Local-first?
- Group data model: shared graph instance, or individual graphs queried together?
- How does a "group" form? Invite-based? Code? Organic?
