import api from "./api";

export interface MarketStat {
  market_type: string;
  total: number;
  hits: number;
  hit_rate: number | null;
}

export interface IdeaTypeStat {
  idea_type: string;
  count: number;
}

export interface TipsterStat {
  id: number;
  name: string;
  display_name: string | null;
  total_ideas: number;
  actionable_ideas: number;
  evaluated_ideas: number;
  hits: number;
  hit_rate: number | null;
}

export interface DashboardData {
  total_tipsters: number;
  active_tipsters: number;
  total_videos: number;
  analyzed_videos: number;
  total_ideas: number;
  actionable_ideas: number;
  evaluated_ideas: number;
  overall_hit_rate: number | null;
  ideas_by_market: MarketStat[];
  ideas_by_type: IdeaTypeStat[];
  top_tipsters: TipsterStat[];
}

export async function fetchDashboard(): Promise<DashboardData> {
  const { data } = await api.get<DashboardData>("/dashboard");
  return data;
}
