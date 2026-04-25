import api from "./api";

export interface GameResultPayload {
  game_id: number;
  home_score?: number | null;
  away_score?: number | null;
  both_teams_scored?: boolean | null;
  total_goals?: number | null;
  corners_total?: number | null;
  cards_total?: number | null;
  result_source?: string | null;
}

export interface GameResult {
  id: number;
  game_id: number;
  home_score: number | null;
  away_score: number | null;
  both_teams_scored: boolean | null;
  total_goals: number | null;
  corners_total: number | null;
  cards_total: number | null;
  result_source: string | null;
  is_manual: boolean;
  created_at: string;
}

export async function createResult(payload: GameResultPayload): Promise<GameResult> {
  const { data } = await api.post<GameResult>("/game-results", payload);
  return data;
}

export async function fetchResult(gameId: number): Promise<GameResult> {
  const { data } = await api.get<GameResult>(`/game-results/${gameId}`);
  return data;
}
