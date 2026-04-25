"use client";

import Link from "next/link";
import AppLayout from "../../../components/AppLayout";
import LoadingSpinner from "../../../components/LoadingSpinner";
import EmptyState from "../../../components/EmptyState";
import Badge from "../../../components/Badge";
import { useApi } from "../../../hooks/useApi";
import { fetchDashboard } from "../../../services/dashboard";
import type { TipsterStat } from "../../../services/dashboard";

function HitBar({ hits, total }: { hits: number; total: number }) {
  const pct = total ? Math.round((hits / total) * 100) : 0;
  const color =
    pct >= 60 ? "bg-green-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-600 w-10 text-right">{pct}%</span>
    </div>
  );
}

function TipsterRow({ t, rank }: { t: TipsterStat; rank: number }) {
  const hitRate =
    t.hit_rate != null ? Math.round(t.hit_rate * 100) : null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-gray-300 w-6 text-center">
            {rank}
          </span>
          <div>
            <Link
              href={`/tipsters/${t.id}`}
              className="font-semibold text-gray-900 hover:text-indigo-600"
            >
              {t.display_name ?? t.name}
            </Link>
            <p className="text-xs text-gray-500">
              {t.total_ideas} ideias · {t.actionable_ideas} acionáveis
            </p>
          </div>
        </div>
        <Badge
          label={
            hitRate != null ? `${hitRate}% acerto` : "sem dados"
          }
          color={
            hitRate == null
              ? "gray"
              : hitRate >= 60
              ? "green"
              : hitRate >= 40
              ? "yellow"
              : "red"
          }
        />
      </div>

      <div className="grid grid-cols-3 gap-3 text-center text-xs mb-3">
        <div>
          <p className="text-base font-bold text-gray-900">{t.actionable_ideas}</p>
          <p className="text-gray-500">acionáveis</p>
        </div>
        <div>
          <p className="text-base font-bold text-gray-900">{t.evaluated_ideas}</p>
          <p className="text-gray-500">avaliadas</p>
        </div>
        <div>
          <p className="text-base font-bold text-gray-900">{t.hits}</p>
          <p className="text-gray-500">acertos</p>
        </div>
      </div>

      {t.evaluated_ideas > 0 && (
        <HitBar hits={t.hits} total={t.evaluated_ideas} />
      )}
    </div>
  );
}

export default function TipsterComparativoPage() {
  const { data: dash, loading, error } = useApi(() => fetchDashboard(), []);

  const tipsters = dash?.top_tipsters ?? [];
  const sorted = [...tipsters].sort(
    (a, b) => (b.hit_rate ?? -1) - (a.hit_rate ?? -1)
  );

  return (
    <AppLayout>
      <div className="mb-6">
        <Link href="/tipsters" className="text-sm text-indigo-600 hover:underline">
          Tipsters
        </Link>
        <span className="text-gray-400 mx-2">/</span>
        <span className="text-sm text-gray-700">Comparativo</span>
      </div>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Comparativo de Tipsters</h1>
        <p className="text-sm text-gray-500 mt-1">
          Ranking por taxa de acerto (mínimo de ideias avaliadas).
        </p>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {!loading && !error && tipsters.length === 0 && (
        <EmptyState message="Nenhum tipster com dados suficientes ainda." />
      )}

      {/* Summary bar */}
      {dash && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{dash.total_tipsters}</p>
            <p className="text-xs text-gray-500 mt-1">Tipsters cadastrados</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{dash.actionable_ideas}</p>
            <p className="text-xs text-gray-500 mt-1">Ideias acionáveis</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">
              {dash.overall_hit_rate != null
                ? `${Math.round(dash.overall_hit_rate * 100)}%`
                : "—"}
            </p>
            <p className="text-xs text-gray-500 mt-1">Taxa de acerto geral</p>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {sorted.map((t, i) => (
          <TipsterRow key={t.id} t={t} rank={i + 1} />
        ))}
      </div>
    </AppLayout>
  );
}
