"use client";

import { useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import AppLayout from "../../components/AppLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import EmptyState from "../../components/EmptyState";
import Badge from "../../components/Badge";
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
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Jogos</h1>
          <p className="text-sm text-gray-500 mt-1">Jogos por data com ideias dos tipsters.</p>
        </div>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {!loading && !error && (games ?? []).length === 0 && (
        <EmptyState message="Nenhum jogo encontrado para essa data." />
      )}

      <div className="space-y-4">
        {(games ?? []).map((game) => (
          <div key={game.id} className="bg-white rounded-lg border border-gray-200">
            <Link
              href={`/games/${game.id}`}
              className="flex items-center justify-between px-5 py-4 hover:bg-gray-50"
            >
              <div>
                <p className="font-semibold text-gray-900">
                  {game.home_team?.name ?? "?"} vs {game.away_team?.name ?? "?"}
                </p>
                <div className="flex items-center gap-3 mt-1">
                  {game.competition && (
                    <span className="text-xs text-gray-400">{game.competition.name}</span>
                  )}
                  {game.scheduled_at && (
                    <span className="text-xs text-gray-400">
                      {format(new Date(game.scheduled_at), "HH:mm")}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge label={`${game.ideas.length} ideias`} color="gray" />
                <Badge
                  label={`${game.ideas.filter((i) => i.is_actionable).length} acion.`}
                  color="indigo"
                />
              </div>
            </Link>

            {game.ideas.length > 0 && (
              <div className="border-t border-gray-100 divide-y divide-gray-100">
                {game.ideas.slice(0, 3).map((idea) => (
                  <div key={idea.id} className="px-5 py-3 flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 truncate">
                        {idea.belief_text ?? idea.rationale_text ?? idea.source_excerpt ?? "—"}
                      </p>
                      {idea.entry_text && (
                        <p className="text-xs text-green-700 mt-0.5 truncate">
                          Entrada: {idea.entry_text}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <Badge
                        label={idea.idea_type.replace(/_/g, " ")}
                        color={IDEA_TYPE_COLORS[idea.idea_type] ?? "gray"}
                      />
                      <Badge label={idea.market_type.replace(/_/g, " ")} color="blue" />
                    </div>
                  </div>
                ))}
                {game.ideas.length > 3 && (
                  <div className="px-5 py-2 text-xs text-indigo-600">
                    <Link href={`/games/${game.id}`}>
                      +{game.ideas.length - 3} ideias — ver tudo
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </AppLayout>
  );
}
