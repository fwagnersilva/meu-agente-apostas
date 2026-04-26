import api from "./api";

export interface Channel {
  id: number;
  tipster_id: number;
  platform: string;
  platform_channel_id: string;
  status: string;
}

export async function createChannel(payload: {
  tipster_id: number;
  platform: string;
  platform_channel_id: string;
}): Promise<Channel> {
  const { data } = await api.post<Channel>("/channels", payload);
  return data;
}
