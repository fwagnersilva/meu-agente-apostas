"use client";

import Link from "next/link";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import AppLayout from "../../components/AppLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import Badge from "../../components/Badge";
import { useApi } from "../../hooks/useApi";
import { fetchDashboard } from "../../services/dashboard";
import { fetchGames } from "../../services/games";
import { fetchVideos } from "../../services/videos";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function HitBar({ hits, total }: { hits: number; total: number }) {
  const pct = total ? Math.round((hits / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div
          className="bg-indigo-500 h-2 rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-600 w-10 text-right">{pct}%</span>
    </div>
  );
}

export default function DashboardPage() {
  const today = format(new Date(), "yyyy-MM-dd");
  const { data: dash, loading: dLoading } = useApi(() => fetchDashboard(), []);
  const { data: games, loading: gLoading } = useApi(() => fetchGames(today), [today]);
  const { data: videos, loading: vLoading } = useApi(() => fetchVideos({ limit: 5 }), []);

  const loading = dLoading || gLoading || vLoading;

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          {format(new Date(), "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR })}
        </p>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Global stats */}
          {dash && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard
                label="Tipsters ativos"
                value={dash.active_tipsters}
                sub={`de ${dash.total_tipsters} total`}
              />
              <StatCard
                label="Vídeos analisados"
                value={dash.analyzed_videos}
                sub={`de ${dash.total_videos} ingeridos`}
              />
              <StatCard
                label="Ideias acionáveis"
                value={dash.actionable_ideas}
                sub={`de ${dash.total_ideas} total`}
              />
              <StatCard
                label="Taxa de acerto geral"
                value={
                  dash.overall_hit_rate != null
                    ? `${Math.round(dash.overall_hit_rate * 100)}%`
                    : "—"
                }
                sub={`${dash.evaluated_ideas} avaliadas`}
              />
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Top tipsters */}
            {dash && dash.top_tipsters.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-semibold text-gray-800">Top Tipsters</h2>
                  <Link href="/tipsters/comparativo" className="text-xs text-indigo-600 hover:underline">
                    Comparativo completo
                  </Link>
                </div>
                <div className="space-y-3">
                  {dash.top_tipsters.slice(0, 5).map((t) => (
                    <div key={t.id}>
                      <div className="flex items-center justify-between mb-1">
                        <Link
                          href={`/tipsters/${t.id}`}
                          className="text-sm text-gray-900 hover:text-indigo-600"
                        >
                          {t.display_name ?? t.name}
                        </Link>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span>{t.actionable_ideas} acion.</span>
                          {t.evaluated_ideas > 0 && (
                            <span className="font-medium text-gray-700">
                              {t.hits}/{t.evaluated_ideas}
                            </span>
                          )}
                        </div>
                      </div>
                      <HitBar hits={t.hits} total={t.evaluated_ideas} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Ideas by market */}
            {dash && dash.ideas_by_market.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-800 mb-4">Mercados mais usados</h2>
                <div className="space-y-3">
                  {dash.ideas_by_market.slice(0, 6).map((m) => (
                    <div key={m.market_type}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-700">
                          {m.market_type.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs text-gray-500">
                          {m.total} ideias
                          {m.hit_rate != null && (
                            <span className="ml-1 text-indigo-600">
                              · {Math.round(m.hit_rate * 100)}% acerto
                            </span>
                          )}
                        </span>
                      </div>
                      <HitBar hits={m.hits} total={m.total} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Today's games */}
          <section className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-gray-800">Jogos de hoje</h2>
              <Link href="/games" className="text-sm text-indigo-600 hover:underline">
                Ver todos
              </Link>
            </div>
            {(games ?? []).length === 0 ? (
              <p className="text-sm text-gray-400">Nenhum jogo registrado para hoje.</p>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
                {(games ?? []).slice(0, 5).map((game) => (
                  <Link
                    key={game.id}
                    href={`/games/${game.id}`}
                    className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {game.home_team?.name ?? "?"} vs {game.away_team?.name ?? "?"}
                      </p>
                      {game.competition && (
                        <p className="text-xs text-gray-400">{game.competition.name}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">{game.ideas.length} ideias</span>
                      <Badge
                        label={`${game.ideas.filter((i) => i.is_actionable).length} acion.`}
                        color="indigo"
                      />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>

          {/* Recent videos */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-gray-800">Vídeos recentes</h2>
              <Link href="/videos" className="text-sm text-indigo-600 hover:underline">
                Ver todos
              </Link>
            </div>
            {(videos ?? []).length === 0 ? (
              <p className="text-sm text-gray-400">Nenhum vídeo processado ainda.</p>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
                {(videos ?? []).map((v) => (
                  <Link
                    key={v.id}
                    href={`/videos/${v.id}`}
                    className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
                  >
                    <p className="text-sm text-gray-900 truncate max-w-md">{v.title}</p>
                    <Badge
                      label={v.status}
                      color={
                        v.status === "analyzed" ? "green" : v.status === "failed" ? "red" : "yellow"
                      }
                    />
                  </Link>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </AppLayout>
  );
}
