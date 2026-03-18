const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("crate_token");
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    if (res.status === 401) {
      // Could redirect to login here
    }
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  return res.json();
}

/** For file uploads (no Content-Type header — browser sets multipart boundary) */
async function fetchApiUpload<T>(path: string, body: FormData): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// --- Types ---
import type {
  SearchResult,
  AddResponse,
  CollectionItem,
  TaskStatus,
  QueryResponse,
  CollectionStats,
  GraphData,
  ExploreResult,
} from "./types";

// --- Auth ---

export interface AuthResponse {
  token: string;
  user_id: string;
  name: string;
  email: string;
}

export async function register(email: string, name: string, password: string): Promise<AuthResponse> {
  return fetchApi("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, name, password }),
  });
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return fetchApi("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(): Promise<{ user_id: string; name: string; email: string }> {
  return fetchApi("/auth/me");
}

// --- Collection ---

export async function searchRelease(artist: string, title: string): Promise<SearchResult[]> {
  return fetchApi("/collection/search", {
    method: "POST",
    body: JSON.stringify({ artist, title }),
  });
}

export async function addRecord(
  discogs_id: number,
  musicbrainz_id?: string | null,
): Promise<AddResponse> {
  return fetchApi("/collection/add", {
    method: "POST",
    body: JSON.stringify({ discogs_id, musicbrainz_id }),
  });
}

export async function addRecordAsync(
  discogs_id: number,
  musicbrainz_id?: string | null,
): Promise<TaskStatus> {
  return fetchApi("/collection/add/async", {
    method: "POST",
    body: JSON.stringify({ discogs_id, musicbrainz_id }),
  });
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  return fetchApi(`/collection/task/${taskId}`);
}

export async function getCollection(): Promise<CollectionItem[]> {
  return fetchApi("/collection/");
}

export async function getRecord(discogs_id: number) {
  return fetchApi(`/collection/record/${discogs_id}`);
}

export async function deleteRecord(discogs_id: number): Promise<void> {
  await fetchApi(`/collection/record/${discogs_id}`, { method: "DELETE" });
}

export async function importCsv(file: File, quick = true) {
  const formData = new FormData();
  formData.append("file", file);
  return fetchApiUpload(`/collection/import/csv?quick=${quick}`, formData);
}

// --- Query ---

export async function queryGraph(
  question: string,
  group_id?: string
): Promise<QueryResponse> {
  return fetchApi("/query/", {
    method: "POST",
    body: JSON.stringify({ question, group_id }),
  });
}

// --- Graph ---

export async function getStats(): Promise<CollectionStats> {
  return fetchApi("/graph/stats");
}

export async function getSharedPersonnel() {
  return fetchApi("/graph/shared-personnel");
}

export async function getHubs(label = "Artist", limit = 15) {
  return fetchApi(`/graph/hubs?label=${label}&limit=${limit}`);
}

export async function getFullGraph(): Promise<GraphData> {
  return fetchApi("/graph/full");
}

export async function getGroupGraph(groupId: string): Promise<any> {
  return fetchApi(`/graph/group/${groupId}`);
}

export async function explorNode(
  node_label: string,
  node_name: string
): Promise<ExploreResult> {
  return fetchApi("/graph/explore", {
    method: "POST",
    body: JSON.stringify({ node_label, node_name }),
  });
}

export async function findPath(album_id_1: number, album_id_2: number) {
  return fetchApi("/graph/path", {
    method: "POST",
    body: JSON.stringify({ album_id_1, album_id_2 }),
  });
}

// --- Groups ---

export interface GroupResponse {
  id: string;
  name: string;
  invite_code: string;
  role: string;
  member_count: number;
}

export async function createGroup(name: string): Promise<GroupResponse> {
  return fetchApi("/groups/", { method: "POST", body: JSON.stringify({ name }) });
}

export async function joinGroup(invite_code: string): Promise<GroupResponse> {
  return fetchApi("/groups/join", { method: "POST", body: JSON.stringify({ invite_code }) });
}

export async function listGroups(): Promise<GroupResponse[]> {
  return fetchApi("/groups/");
}

export async function getGroupMembers(groupId: string) {
  return fetchApi(`/groups/${groupId}/members`);
}

// --- Group Insights ---

export async function getGroupStats(groupId: string) {
  return fetchApi(`/groups/${groupId}/insights/stats`);
}

export async function getGroupOverlap(groupId: string) {
  return fetchApi(`/groups/${groupId}/insights/overlap`);
}

export async function getGroupBridges(groupId: string) {
  return fetchApi(`/groups/${groupId}/insights/bridges`);
}

export async function getGroupBlindSpots(groupId: string) {
  return fetchApi(`/groups/${groupId}/insights/blind-spots`);
}

export async function getGroupTasteDistance(groupId: string) {
  return fetchApi(`/groups/${groupId}/insights/taste-distance`);
}

// --- Feed ---

export interface FeedEvent {
  id: string;
  user_id: string;
  group_id: string | null;
  event_type: string;
  discogs_id: number | null;
  title: string;
  body: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export async function getMyFeed(limit = 50): Promise<FeedEvent[]> {
  return fetchApi(`/feed/?limit=${limit}`);
}

export async function getGroupFeed(groupId: string, limit = 50): Promise<FeedEvent[]> {
  return fetchApi(`/feed/group/${groupId}?limit=${limit}`);
}

// --- Annotations ---

export interface AnnotationData {
  id: string;
  user_id: string;
  user_name: string;
  node_label: string;
  node_name: string;
  text: string;
  created_at: string;
}

export async function createAnnotation(node_label: string, node_name: string, text: string): Promise<AnnotationData> {
  return fetchApi("/annotations/", {
    method: "POST",
    body: JSON.stringify({ node_label, node_name, text }),
  });
}

export async function getAnnotations(node_label: string, node_name: string): Promise<AnnotationData[]> {
  return fetchApi(`/annotations/node/${node_label}/${encodeURIComponent(node_name)}`);
}
