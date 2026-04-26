import api from "./api";

export interface Channel {
  id: number;
  tipster_id: number;
  channel_name: string;
  channel_url: string;
  channel_external_id: string | null;
  is_active: boolean;
  monitoring_status: string;
}

export async function createChannel(payload: {
  tipster_id: number;
  channel_name: string;
  channel_url: string;
  channel_external_id?: string;
}): Promise<Channel> {
  const { data } = await api.post<Channel>("/channels", payload);
  return data;
}
