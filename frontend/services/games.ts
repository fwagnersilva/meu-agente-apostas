import api from "./api";

export interface Team {
  id: number;
  name: string;
  country: string | null;
}

export interface Competition {
  id: number;
  name: string;
  country: string | null;
}

export interface IdeaCondition {
  id: number;
  condition_type: string;
  text: string;
  is_inferred: boolean;
}

export interface IdeaReason {
  id: number;
  category: string;
  text: string;
}

export interface IdeaLabel {
  id: number;
  label: string;
}

export interface Idea {
  id: number;
  game_id: number;
  video_id: number;
  tipster_id: number;
  idea_type: string;
  market_type: string;
  selection_label: string | null;
  sentiment_direction: string;
  confidence_band: string;
  confidence_expression_text: string | null;
  belief_text: string | null;
  fear_text: string | null;
  entry_text: string | null;
  avoid_text: string | null;
  rationale_text: string | null;
  source_excerpt: string | null;
  is_actionable: boolean;
  needs_review: boolean;
  extraction_confidence: number;
  review_status: string;
  conditions: IdeaCondition[];
  reasons: IdeaReason[];
  labels: IdeaLabel[];
  created_at: string;
}

export interface Game {
  id: number;
  home_team: Team | null;
  away_team: Team | null;
  competition: Competition | null;
  scheduled_at: string | null;
  status: string;
  created_at: string;
  ideas: Idea[];
}

export async function fetchGames(date?: string): Promise<Game[]> {
  const params = date ? { date } : {};
  const { data } = await api.get<Game[]>("/games", { params });
  return data;
}

export async function fetchGame(id: number): Promise<Game> {
  const { data } = await api.get<Game>(`/games/${id}`);
  return data;
}
