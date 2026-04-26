"use client";

import { useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import AppLayout from "../../components/AppLayout";
import Card from "../../components/Card";
import Badge from "../../components/Badge";
import LoadingSpinner from "../../components/LoadingSpinner";
import { useApi } from "../../hooks/useApi";
import { fetchVideos } from "../../services/videos";

const STATUS_OPTIONS = ["", "queued", "processing", "analyzed", "failed"];
const STATUS_LABELS: Record<string, string> = {
  "": "Todos", queued: "Na fila", processing: "Processando", analyzed: "Analisado", failed: "Falhou",
};

export default function VideosPage() {
  const [status, setStatus] = useState("");
  const { data: videos, loading, error } = useApi(
    () => fetchVideos({ status: status || undefined, limit: 100 }),
    [status]
  );

  return (
    <AppLayout>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Vídeos</h1>
          <p className="text-sm text-slate-500 mt-0.5">Todos os vídeos ingeridos pelo sistema.</p>
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {!loading && !error && (videos ?? []).length === 0 && (
        <Card className="p-10 text-center">
          <p className="text-slate-400 text-sm">Nenhum vídeo encontrado.</p>
        </Card>
      )}

      {!loading && !error && (videos ?? []).length > 0 && (
        <Card>
          <div className="divide-y divide-slate-100">
            {(videos ?? []).map((v) => (
              <Link key={v.id} href={`/videos/${v.id}`}
                className="flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition-colors gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">{v.title}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {v.published_at ? format(new Date(v.published_at), "dd/MM/yyyy") : "sem data"}
                  </p>
                </div>
                <Badge
                  label={STATUS_LABELS[v.status] ?? v.status}
                  color={v.status === "analyzed" ? "green" : v.status === "failed" ? "red" : v.status === "processing" ? "blue" : "yellow"}
                />
              </Link>
            ))}
          </div>
        </Card>
      )}
    </AppLayout>
  );
}
