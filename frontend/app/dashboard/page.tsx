"use client";

import Link from "next/link";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import AppLayout from "../../components/AppLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import Badge from "../../components/Badge";
import { useApi } from "../../hooks/useApi";
import { fetchGames } from "../../services/games";
import { fetchTipsters } from "../../services/tipsters";
import { fetchVideos } from "../../services/videos";

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const today = format(new Date(), "yyyy-MM-dd");
  const { data: games, loading: gLoading } = useApi(() => fetchGames(today), [today]);
  const { data: tipsters, loading: tLoading } = useApi(() => fetchTipsters(), []);
  const { data: videos, loading: vLoading } = useApi(() => fetchVideos({ limit: 5 }), []);

  const loading = gLoading || tLoading || vLoading;
  const todayGames = games ?? [];
  const recentVideos = videos ?? [];

  const totalIdeas = todayGames.reduce((acc, g) => acc + g.ideas.length, 0);
  const actionableIdeas = todayGames.reduce(
    (acc, g) => acc + g.ideas.filter((i) => i.is_actionable).length,
    0
  );
  const activeTipsters = (tipsters ?? []).filter((t) => t.status === "active").length;

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
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Jogos hoje" value={todayGames.length} />
            <StatCard label="Ideias hoje" value={totalIdeas} />
            <StatCard label="Acionáveis hoje" value={actionableIdeas} />
            <StatCard label="Tipsters ativos" value={activeTipsters} />
          </div>

          <section className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-gray-800">Jogos de hoje</h2>
              <Link href="/games" className="text-sm text-indigo-600 hover:underline">
                Ver todos
              </Link>
            </div>
            {todayGames.length === 0 ? (
              <p className="text-sm text-gray-400">Nenhum jogo registrado para hoje.</p>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
                {todayGames.slice(0, 5).map((game) => (
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

          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-gray-800">Vídeos recentes</h2>
              <Link href="/videos" className="text-sm text-indigo-600 hover:underline">
                Ver todos
              </Link>
            </div>
            {recentVideos.length === 0 ? (
              <p className="text-sm text-gray-400">Nenhum vídeo processado ainda.</p>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
                {recentVideos.map((v) => (
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
