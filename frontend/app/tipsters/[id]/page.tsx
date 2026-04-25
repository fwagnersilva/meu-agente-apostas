"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import AppLayout from "../../../components/AppLayout";
import LoadingSpinner from "../../../components/LoadingSpinner";
import Badge from "../../../components/Badge";
import { useApi } from "../../../hooks/useApi";
import { fetchTipster } from "../../../services/tipsters";

export default function TipsterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: tipster, loading, error } = useApi(
    () => fetchTipster(Number(id)),
    [id]
  );

  return (
    <AppLayout>
      <div className="mb-6">
        <Link href="/tipsters" className="text-sm text-indigo-600 hover:underline">
          Tipsters
        </Link>
        <span className="text-gray-400 mx-2">/</span>
        <span className="text-sm text-gray-700">{tipster?.display_name ?? tipster?.name ?? "..."}</span>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-red-500 text-sm">{error}</p>}

      {tipster && (
        <>
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {tipster.display_name ?? tipster.name}
                </h1>
                {tipster.bio && (
                  <p className="text-sm text-gray-500 mt-1 max-w-xl">{tipster.bio}</p>
                )}
              </div>
              <Badge
                label={tipster.status}
                color={tipster.status === "active" ? "green" : "gray"}
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{tipster.channels_count}</p>
              <p className="text-xs text-gray-500 mt-1">Canais</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{tipster.ideas_count}</p>
              <p className="text-xs text-gray-500 mt-1">Ideias totais</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{tipster.actionable_ideas_count}</p>
              <p className="text-xs text-gray-500 mt-1">Acionáveis</p>
            </div>
          </div>
        </>
      )}
    </AppLayout>
  );
}
