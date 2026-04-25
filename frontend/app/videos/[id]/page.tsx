"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";
import AppLayout from "../../../components/AppLayout";
import LoadingSpinner from "../../../components/LoadingSpinner";
import Badge from "../../../components/Badge";
import { useApi } from "../../../hooks/useApi";
import { fetchVideo, fetchAnalysesByVideo, reprocessVideo } from "../../../services/videos";

export default function VideoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [reprocessing, setReprocessing] = useState(false);
  const [reprocessMsg, setReprocessMsg] = useState<string | null>(null);

  const { data: video, loading: vLoading } = useApi(() => fetchVideo(Number(id)), [id]);
  const {
    data: analyses,
    loading: aLoading,
    refetch: refetchAnalyses,
  } = useApi(() => fetchAnalysesByVideo(Number(id)), [id]);

  async function handleReprocess() {
    setReprocessing(true);
    setReprocessMsg(null);
    try {
      await reprocessVideo(Number(id));
      setReprocessMsg("Vídeo enfileirado para reprocessamento.");
      setTimeout(() => refetchAnalyses(), 2000);
    } catch {
      setReprocessMsg("Erro ao enfileirar reprocessamento.");
    } finally {
      setReprocessing(false);
    }
  }

  const loading = vLoading || aLoading;
  const latestAnalysis = (analyses ?? [])[0];

  return (
    <AppLayout>
      <div className="mb-6">
        <Link href="/videos" className="text-sm text-indigo-600 hover:underline">
          Vídeos
        </Link>
        <span className="text-gray-400 mx-2">/</span>
        <span className="text-sm text-gray-700 truncate max-w-md inline-block align-bottom">
          {video?.title ?? "..."}
        </span>
      </div>

      {loading && <LoadingSpinner />}

      {video && (
        <>
          <div className="bg-white rounded-lg border border-gray-200 p-5 mb-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h1 className="text-lg font-bold text-gray-900">{video.title}</h1>
                <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                  {video.published_at && (
                    <span>{format(new Date(video.published_at), "dd/MM/yyyy")}</span>
                  )}
                  <a
                    href={video.youtube_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:underline"
                  >
                    Abrir no YouTube
                  </a>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  label={video.status}
                  color={
                    video.status === "analyzed"
                      ? "green"
                      : video.status === "failed"
                      ? "red"
                      : "yellow"
                  }
                />
                <button
                  onClick={handleReprocess}
                  disabled={reprocessing}
                  className="text-xs text-indigo-600 border border-indigo-300 rounded px-2 py-1 hover:bg-indigo-50 disabled:opacity-50"
                >
                  {reprocessing ? "Enfileirando..." : "Reprocessar"}
                </button>
              </div>
            </div>
            {reprocessMsg && (
              <p className="mt-2 text-sm text-green-600">{reprocessMsg}</p>
            )}
          </div>

          {/* Latest analysis */}
          {latestAnalysis && (
            <div className="mb-6">
              <h2 className="text-base font-semibold text-gray-800 mb-3">Análise mais recente</h2>
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex flex-wrap gap-1.5">
                    <Badge
                      label={latestAnalysis.analysis_status.replace(/_/g, " ")}
                      color={
                        latestAnalysis.analysis_status === "analyzed_with_matches"
                          ? "green"
                          : latestAnalysis.analysis_status === "failed"
                          ? "red"
                          : latestAnalysis.analysis_status === "irrelevant"
                          ? "gray"
                          : "yellow"
                      }
                    />
                    {latestAnalysis.content_scope && (
                      <Badge label={latestAnalysis.content_scope.replace(/_/g, " ")} color="blue" />
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {latestAnalysis.analyzed_at
                      ? format(new Date(latestAnalysis.analyzed_at), "dd/MM HH:mm")
                      : "—"}
                  </span>
                </div>

                {latestAnalysis.summary_text && (
                  <p className="text-sm text-gray-700 mb-4">{latestAnalysis.summary_text}</p>
                )}

                <div className="grid grid-cols-4 gap-3 text-center text-xs">
                  <div>
                    <p className="text-lg font-bold text-gray-900">{latestAnalysis.games_detected_count}</p>
                    <p className="text-gray-500">jogos</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-gray-900">{latestAnalysis.ideas_detected_count}</p>
                    <p className="text-gray-500">ideias</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-gray-900">{latestAnalysis.actionable_ideas_count}</p>
                    <p className="text-gray-500">acionáveis</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-gray-900">{latestAnalysis.no_value_count}</p>
                    <p className="text-gray-500">sem valor</p>
                  </div>
                </div>

                {latestAnalysis.transcript && latestAnalysis.transcript.normalized_transcript_text && (
                  <details className="mt-4">
                    <summary className="text-xs text-indigo-600 cursor-pointer hover:underline">
                      Ver transcrição ({latestAnalysis.transcript.transcript_source})
                    </summary>
                    <pre className="mt-2 text-xs text-gray-600 bg-gray-50 rounded p-3 whitespace-pre-wrap max-h-64 overflow-auto">
                      {latestAnalysis.transcript.normalized_transcript_text}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          )}

          {/* Analysis history */}
          {(analyses ?? []).length > 1 && (
            <div>
              <h2 className="text-base font-semibold text-gray-800 mb-3">
                Histórico de análises ({(analyses ?? []).length})
              </h2>
              <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
                {(analyses ?? []).map((a) => (
                  <div key={a.id} className="flex items-center justify-between px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Badge
                        label={a.analysis_status.replace(/_/g, " ")}
                        color={
                          a.analysis_status.includes("analyzed") ? "green" : "red"
                        }
                      />
                      <span className="text-xs text-gray-500">
                        {a.model_version ?? "—"} / {a.prompt_version ?? "—"}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">
                      {a.created_at ? format(new Date(a.created_at), "dd/MM/yyyy HH:mm") : "—"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </AppLayout>
  );
}
