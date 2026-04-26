"use client";

import Link from "next/link";
import AppLayout from "../../../components/AppLayout";
import Card from "../../../components/Card";
import Badge from "../../../components/Badge";
import LoadingSpinner from "../../../components/LoadingSpinner";
import { useApi } from "../../../hooks/useApi";
import { fetchDashboard } from "../../../services/dashboard";
import type { TipsterStat } from "../../../services/dashboard";

function HitBar({ hits, total }: { hits: number; total: number }) {
  const pct = total ? Math.round((hits / total) * 100) : 0;
  const color = pct >= 60 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 bg-slate-100 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 tabular-nums w-8 text-right">{pct}%</span>
    </div>
  );
}

function TipsterRow({ t, rank }: { t: TipsterStat; rank: number }) {
  const hitRate = t.hit_rate != null ? Math.round(t.hit_rate * 100) : null;

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold text-slate-200 w-7 tabular-nums">{rank}</span>
          <div>
            <Link href={`/tipsters/${t.id}`} className="text-sm font-semibold text-slate-800 hover:text-indigo-600">
              {t.display_name ?? t.name}
            </Link>
            <p className="text-xs text-slate-400 mt-0.5">{t.total_ideas} ideias · {t.actionable_ideas} acionáveis</p>
          </div>
        </div>
        <Badge
          label={hitRate != null ? `${hitRate}% acerto` : "sem dados"}
          color={hitRate == null ? "gray" : hitRate >= 60 ? "green" : hitRate >= 40 ? "yellow" : "red"}
        />
      </div>

      <div className="grid grid-cols-3 gap-3 text-center text-xs mb-3 bg-slate-50 rounded-lg p-3">
        <div>
          <p className="text-base font-bold text-slate-900">{t.actionable_ideas}</p>
          <p className="text-slate-500">acionáveis</p>
        </div>
        <div>
          <p className="text-base font-bold text-slate-900">{t.evaluated_ideas}</p>
          <p className="text-slate-500">avaliadas</p>
        </div>
        <div>
          <p className="text-base font-bold text-slate-900">{t.hits}</p>
          <p className="text-slate-500">acertos</p>
        </div>
      </div>

      {t.evaluated_ideas > 0 && <HitBar hits={t.hits} total={t.evaluated_ideas} />}
    </Card>
  );
}

export default function TipsterComparativoPage() {
  const { data: dash, loading, error } = useApi(() => fetchDashboard(), []);

  const tipsters = dash?.top_tipsters ?? [];
  const sorted = [...tipsters].sort((a, b) => (b.hit_rate ?? -1) - (a.hit_rate ?? -1));

  return (
    <AppLayout>
      <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-6">
        <Link href="/tipsters" className="text-indigo-600 hover:underline">Tipsters</Link>
        <span>/</span>
        <span>Comparativo</span>
      </div>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Comparativo de Tipsters</h1>
          <p className="text-sm text-slate-500 mt-0.5">Ranking por taxa de acerto.</p>
        </div>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {dash && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: "Tipsters", value: dash.total_tipsters },
            { label: "Ideias acionáveis", value: dash.actionable_ideas },
            { label: "Taxa de acerto geral", value: dash.overall_hit_rate != null ? `${Math.round(dash.overall_hit_rate * 100)}%` : "—" },
          ].map(({ label, value }) => (
            <Card key={label} className="p-4 text-center">
              <p className="text-2xl font-bold text-slate-900">{value}</p>
              <p className="text-xs text-slate-500 mt-1">{label}</p>
            </Card>
          ))}
        </div>
      )}

      {!loading && !error && tipsters.length === 0 && (
        <Card className="p-10 text-center">
          <p className="text-slate-400 text-sm">Nenhum tipster com dados suficientes ainda.</p>
        </Card>
      )}

      <div className="space-y-3">
        {sorted.map((t, i) => <TipsterRow key={t.id} t={t} rank={i + 1} />)}
      </div>
    </AppLayout>
  );
}
