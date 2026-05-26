// Shared types between frontend and backend (kept loose because the bot graph
// is user-authored data and not strictly typed).

export type Role = "admin" | "mama";

export interface FlowSummary {
  id: string;
  name: string;
  description: string | null;
  is_published: boolean;
  version: number;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BlockNode {
  id: string;
  type: string;
  params: Record<string, unknown>;
  // List-based routing: "next" -> the id of the block to jump to.
  next?: string | null;
  // UI-only hints (kept in graph so the layout survives a roundtrip).
  position?: { x: number; y: number };
}

export interface FlowGraph {
  nodes: BlockNode[];
  edges?: { id: string; source: string; target: string; label?: string }[];
}

export interface Flow extends FlowSummary {
  graph: FlowGraph;
}

export interface OutfitImage {
  id: number;
  storage_path: string;
  sort_order: number;
}

export interface Outfit {
  id: number;
  title: string;
  description: string | null;
  colors: string;
  styles: string;
  seasons: string;
  occasions: string;
  body_types: string;
  budgets: string;
  shoot_types: string;
  price_hint: string | null;
  external_url: string | null;
  pinterest_url: string | null;
  tags: Record<string, unknown> | null;
  sort_order: number;
  is_published: boolean;
  outfit_images?: OutfitImage[];
}

export interface Course {
  id: number;
  slug: string;
  title: string;
  description: string | null;
  storage_path: string | null;
  cover_path: string | null;
  preview_pages: number;
  is_published: boolean;
  sort_order: number;
}

export interface Booking {
  id: number;
  telegram_id: number | null;
  telegram_username: string | null;
  full_name: string | null;
  phone: string | null;
  preferred_date: string | null;
  shoot_type: string | null;
  notes: string | null;
  payload: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export interface StatsOverview {
  since: string;
  users_total: number;
  users_new: number;
  bookings_total: number;
  bookings_unread: number;
  events_by_type: Record<string, number>;
  messages_per_day: [string, number][];
  pdf_generated: number;
}
