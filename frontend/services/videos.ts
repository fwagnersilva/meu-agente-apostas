import api from "./api";

export interface Video {
  id: number;
  channel_id: number;
  youtube_video_id: string;
  youtube_url: string;
  title: string;
  description: string | null;
  thumbnail_url: string | null;
  published_at: string | null;
  duration_seconds: number | null;
  status: string;
  created_at: string;
}

export interface TranscriptSegment {
  id: number;
  segment_type: string;
  raw_text: string;
  normalized_text: string;
  start_seconds: number | null;
  end_seconds: number | null;
}

export interface VideoTranscript {
  id: number;
  transcript_source: string;
  language_code: string | null;
  has_timestamps: boolean;
  normalized_transcript_text: string | null;
  segments: TranscriptSegment[];
}

export interface VideoAnalysis {
  id: number;
  video_id: number;
  analysis_url_slug: string | null;
  analyzed_at: string | null;
  analysis_status: string;
  content_scope: string | null;
  summary_text: string | null;
  games_detected_count: number;
  ideas_detected_count: number;
  actionable_ideas_count: number;
  warnings_count: number;
  no_value_count: number;
  review_status: string;
  model_version: string | null;
  prompt_version: string | null;
  schema_version: string | null;
  created_at: string;
  transcript: VideoTranscript | null;
}

export interface VideoListParams {
  channel_id?: number;
  status?: string;
  skip?: number;
  limit?: number;
}

export async function fetchVideos(params?: VideoListParams): Promise<Video[]> {
  const { data } = await api.get<Video[]>("/videos", { params });
  return data;
}

export async function fetchVideo(id: number): Promise<Video> {
  const { data } = await api.get<Video>(`/videos/${id}`);
  return data;
}

export async function fetchAnalysesByVideo(videoId: number): Promise<VideoAnalysis[]> {
  const { data } = await api.get<VideoAnalysis[]>(`/video-analyses/by-video/${videoId}`);
  return data;
}

export async function fetchAnalysis(id: number): Promise<VideoAnalysis> {
  const { data } = await api.get<VideoAnalysis>(`/video-analyses/${id}`);
  return data;
}

export async function reprocessVideo(id: number): Promise<void> {
  await api.post(`/videos/${id}/reprocess`);
}
