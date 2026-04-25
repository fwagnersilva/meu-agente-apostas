import api from "./api";
import type { Idea } from "./games";

export type { Idea };

export interface ReviewPayload {
  action_type: string;
  notes?: string;
  edited_data?: Record<string, unknown>;
}

export interface IdeaReview {
  id: number;
  idea_id: number;
  reviewer_user_id: number;
  action_type: string;
  review_notes: string | null;
  created_at: string;
}

export async function fetchPendingIdeas(skip = 0, limit = 50): Promise<Idea[]> {
  const { data } = await api.get<Idea[]>("/ideas", {
    params: { pending_review: true, skip, limit },
  });
  return data;
}

export async function fetchIdeasByGame(gameId: number): Promise<Idea[]> {
  const { data } = await api.get<Idea[]>("/ideas", { params: { game_id: gameId } });
  return data;
}

export async function reviewIdea(id: number, payload: ReviewPayload): Promise<IdeaReview> {
  const { data } = await api.post<IdeaReview>(`/review/ideas/${id}`, payload);
  return data;
}
