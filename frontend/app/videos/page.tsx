"use client";

import { useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import AppLayout from "../../components/AppLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import EmptyState from "../../components/EmptyState";
import Badge from "../../components/Badge";
import { useApi } from "../../hooks/useApi";
import { fetchVideos } from "../../services/videos";

const STATUS_OPTIONS = ["", "queued", "processing", "analyzed", "failed"];

export default function VideosPage() {
  const [status, setStatus] = useState("");
  const { data: videos, loading, error } = useApi(
    () => fetchVideos({ status: status || undefined, limit: 100 }),
    [status]
  );

  return (
    <AppLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Vídeos</h1>
          <p className="text-sm text-gray-500 mt-1">Todos os vídeos ingeridos pelo sistema.</p>
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s || "Todos os status"}
            </option>
          ))}
        </select>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {!loading && !error && (videos ?? []).length === 0 && (
        <EmptyState message="Nenhum vídeo encontrado." />
      )}

      {!loading && !error && (videos ?? []).length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
          {(videos ?? []).map((v) => (
            <Link
              key={v.id}
              href={`/videos/${v.id}`}
              className="flex items-start justify-between px-5 py-4 hover:bg-gray-50 gap-4"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{v.title}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {v.published_at
                    ? format(new Date(v.published_at), "dd/MM/yyyy")
                    : "sem data"}
                </p>
              </div>
              <Badge
                label={v.status}
                color={
                  v.status === "analyzed"
                    ? "green"
                    : v.status === "failed"
                    ? "red"
                    : v.status === "processing"
                    ? "blue"
                    : "yellow"
                }
              />
            </Link>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
