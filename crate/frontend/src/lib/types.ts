// --- API Types ---

export interface SearchResult {
  discogs_id: number;
  title: string;
  artist: string;
  year: number | null;
  country: string | null;
  cover_url: string | null;
  musicbrainz_id: string | null;
}

export interface AddResponse {
  album_title: string;
  discogs_id: number;
  artists_added: number;
  connections_found: Connection[];
  insights: Insight[] | null;
}

export interface Connection {
  shared_artist?: string;
  shared_label?: string;
  also_on: string[];
  connection_type: string;
}

export interface CollectionItem {
  discogs_id: number;
  title: string;
  year: number | null;
  artists: string[];
}

export interface QueryResponse {
  question: string;
  answer: string;
  cypher: string;
  raw_results: Record<string, unknown>[];
}

export interface Insight {
  type: string;
  text: string;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  result: Record<string, unknown> | null;
}

// --- Graph visualization types ---

export interface GraphNode {
  id: string;
  label: string;
  name: string;
  props: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  props: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface CollectionStats {
  total_albums: number;
  total_artists: number;
  total_labels: number;
  total_genres: number;
  genres: string[];
  labels: string[];
}

export interface ExploreResult {
  node: string;
  label: string;
  connections: {
    source: string;
    relationship: string;
    target_labels: string[];
    target_name: string;
    target_props: Record<string, unknown>;
    rel_props: Record<string, unknown>;
  }[];
}
