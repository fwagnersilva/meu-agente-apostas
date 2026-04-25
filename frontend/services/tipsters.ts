import api from "./api";

export interface Tipster {
  id: number;
  name: string;
  display_name: string | null;
  bio: string | null;
  status: string;
  created_at: string;
}

export interface TipsterWithStats extends Tipster {
  channels_count: number;
  ideas_count: number;
  actionable_ideas_count: number;
}

export async function fetchTipsters(): Promise<TipsterWithStats[]> {
  const { data } = await api.get<TipsterWithStats[]>("/tipsters");
  return data;
}

export async function fetchTipster(id: number): Promise<TipsterWithStats> {
  const { data } = await api.get<TipsterWithStats>(`/tipsters/${id}`);
  return data;
}
