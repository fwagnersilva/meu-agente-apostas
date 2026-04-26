"use client";

import { useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import AppLayout from "../../components/AppLayout";
import Card from "../../components/Card";
import Badge from "../../components/Badge";
import LoadingSpinner from "../../components/LoadingSpinner";
import { useApi } from "../../hooks/useApi";
import { fetchGames } from "../../services/games";

const IDEA_TYPE_COLORS: Record<string, "green" | "red" | "yellow" | "blue" | "gray" | "indigo" | "orange"> = {
  strong_entry: "green",
  possible_entry: "indigo",
  caution: "yellow",
  no_value: "gray",
  avoid_game: "red",
  watch_live: "blue",
  trend_read: "blue",
  risk_alert: "orange",
  condition_based_entry: "indigo",
  contextual_note: "gray",
};

export default function GamesPage() {
  const [date, setDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const { data: games, loading, error } = useApi(() => fetchGames(date), [date]);

  return (
    <AppLayout>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Jogos</h1>
          <p className="text-sm text-slate-500 mt-0.5">Jogos por data com ideias dos tipsters.</p>
        </div>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {!loading && !error && (games ?? []).length === 0 && (
        <Card className="p-10 text-center">
          <p className="text-slate-400 text-sm">Nenhum jogo encontrado para essa data.</p>
        </Card>
      )}

      <div className="space-y-3">
        {(games ?? []).map((game) => (
          <Card key={game.id}>
            <Link href={`/games/${game.id}`}
              className="flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition-colors rounded-t-xl">
              <div>
                <p className="text-sm font-semibold text-slate-800">
                  {game.home_team?.name ?? "?"} <span className="text-slate-400 font-normal">vs</span> {game.away_team?.name ?? "?"}
                </p>
                <div className="flex items-center gap-3 mt-0.5">
                  {game.competition && <span className="text-xs text-slate-400">{game.competition.name}</span>}
                  {game.scheduled_at && (
                    <span className="text-xs text-slate-400">{format(new Date(game.scheduled_at), "HH:mm")}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge label={`${game.ideas.length} ideias`} color="gray" />
                <Badge label={`${game.ideas.filter((i) => i.is_actionable).length} acion.`} color="indigo" />
              </div>
            </Link>

            {game.ideas.length > 0 && (
              <div className="border-t border-slate-100 divide-y divide-slate-100">
                {game.ideas.slice(0, 3).map((idea) => (
                  <div key={idea.id} className="px-5 py-3 flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-600 truncate">
                        {idea.belief_text ?? idea.rationale_text ?? idea.source_excerpt ?? "—"}
                      </p>
                      {idea.entry_text && (
                        <p className="text-xs text-emerald-700 mt-0.5 truncate">Entrada: {idea.entry_text}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <Badge label={idea.idea_type.replace(/_/g, " ")} color={IDEA_TYPE_COLORS[idea.idea_type] ?? "gray"} />
                      <Badge label={idea.market_type.replace(/_/g, " ")} color="blue" />
                    </div>
                  </div>
                ))}
                {game.ideas.length > 3 && (
                  <div className="px-5 py-2">
                    <Link href={`/games/${game.id}`} className="text-xs text-indigo-600 hover:underline">
                      +{game.ideas.length - 3} ideias — ver tudo
                    </Link>
                  </div>
                )}
              </div>
            )}
          </Card>
        ))}
      </div>
    </AppLayout>
  );
}
