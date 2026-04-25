"use client";

import Link from "next/link";
import AppLayout from "../../components/AppLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import EmptyState from "../../components/EmptyState";
import Badge from "../../components/Badge";
import { useApi } from "../../hooks/useApi";
import { fetchTipsters } from "../../services/tipsters";

export default function TipstersPage() {
  const { data: tipsters, loading, error } = useApi(() => fetchTipsters(), []);

  return (
    <AppLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tipsters</h1>
        <p className="text-sm text-gray-500 mt-1">Todos os criadores de conteúdo monitorados.</p>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {!loading && !error && (tipsters ?? []).length === 0 && (
        <EmptyState message="Nenhum tipster cadastrado ainda." />
      )}

      {!loading && !error && (tipsters ?? []).length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
          {(tipsters ?? []).map((t) => (
            <Link
              key={t.id}
              href={`/tipsters/${t.id}`}
              className="flex items-center justify-between px-5 py-4 hover:bg-gray-50"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {t.display_name ?? t.name}
                </p>
                {t.bio && (
                  <p className="text-xs text-gray-400 truncate max-w-sm mt-0.5">{t.bio}</p>
                )}
              </div>
              <div className="flex items-center gap-3 text-right">
                <div className="text-xs text-gray-500">
                  <p>{t.channels_count} canal{t.channels_count !== 1 ? "is" : ""}</p>
                  <p>{t.actionable_ideas_count} ideias acion.</p>
                </div>
                <Badge
                  label={t.status}
                  color={t.status === "active" ? "green" : "gray"}
                />
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
