"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";
import AppLayout from "../../../components/AppLayout";
import LoadingSpinner from "../../../components/LoadingSpinner";
import Badge from "../../../components/Badge";
import EmptyState from "../../../components/EmptyState";
import { useApi } from "../../../hooks/useApi";
import { fetchGame } from "../../../services/games";
import type { Idea } from "../../../services/games";

const SENTIMENT_COLOR: Record<string, "green" | "red" | "yellow" | "gray"> = {
  favorable: "green",
  unfavorable: "red",
  conditional: "yellow",
  neutral: "gray",
};

function IdeaCard({ idea }: { idea: Idea }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex flex-wrap gap-1.5">
          <Badge label={idea.idea_type.replace(/_/g, " ")} color="indigo" />
          <Badge label={idea.market_type.replace(/_/g, " ")} color="blue" />
          {idea.selection_label && (
            <Badge label={idea.selection_label} color="gray" />
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <Badge
            label={idea.confidence_band}
            color={
              idea.confidence_band === "high"
                ? "green"
                : idea.confidence_band === "low"
                ? "red"
                : "yellow"
            }
          />
          <Badge
            label={idea.sentiment_direction}
            color={SENTIMENT_COLOR[idea.sentiment_direction] ?? "gray"}
          />
        </div>
      </div>

      <div className="space-y-1.5 text-sm">
        {idea.belief_text && (
          <div>
            <span className="font-medium text-gray-600">Acredita: </span>
            <span className="text-gray-800">{idea.belief_text}</span>
          </div>
        )}
        {idea.fear_text && (
          <div>
            <span className="font-medium text-gray-600">Teme: </span>
            <span className="text-gray-800">{idea.fear_text}</span>
          </div>
        )}
        {idea.entry_text && (
          <div>
            <span className="font-medium text-green-700">Entrada: </span>
            <span className="text-green-800">{idea.entry_text}</span>
          </div>
        )}
        {idea.avoid_text && (
          <div>
            <span className="font-medium text-red-700">Evitar: </span>
            <span className="text-red-800">{idea.avoid_text}</span>
          </div>
        )}
        {idea.rationale_text && (
          <div>
            <span className="font-medium text-gray-600">Justificativa: </span>
            <span className="text-gray-700">{idea.rationale_text}</span>
          </div>
        )}
      </div>

      {idea.source_excerpt && (
        <blockquote className="mt-3 pl-3 border-l-2 border-gray-300 text-xs text-gray-500 italic">
          {idea.source_excerpt}
        </blockquote>
      )}

      <div className="mt-3 flex items-center gap-2">
        {idea.needs_review && <Badge label="revisão pendente" color="orange" />}
        {!idea.is_actionable && <Badge label="não acionável" color="gray" />}
        <span className="text-xs text-gray-400 ml-auto">
          confiança {Math.round(idea.extraction_confidence * 100)}%
        </span>
      </div>

      {idea.reasons.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {idea.reasons.map((r) => (
            <span
              key={r.id}
              className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
              title={r.text}
            >
              {r.category}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function GameDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: game, loading, error } = useApi(() => fetchGame(Number(id)), [id]);

  return (
    <AppLayout>
      <div className="mb-6">
        <Link href="/games" className="text-sm text-indigo-600 hover:underline">
          Jogos
        </Link>
        <span className="text-gray-400 mx-2">/</span>
        <span className="text-sm text-gray-700">
          {game ? `${game.home_team?.name ?? "?"} vs ${game.away_team?.name ?? "?"}` : "..."}
        </span>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-red-500 text-sm">{error}</p>}

      {game && (
        <>
          <div className="bg-white rounded-lg border border-gray-200 p-5 mb-6">
            <h1 className="text-xl font-bold text-gray-900">
              {game.home_team?.name ?? "?"} vs {game.away_team?.name ?? "?"}
            </h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              {game.competition && <span>{game.competition.name}</span>}
              {game.scheduled_at && (
                <span>
                  {format(new Date(game.scheduled_at), "dd/MM/yyyy HH:mm")}
                </span>
              )}
              <Badge
                label={game.status}
                color={game.status === "finished" ? "green" : "yellow"}
              />
            </div>
          </div>

          <h2 className="text-base font-semibold text-gray-800 mb-3">
            Ideias ({game.ideas.length})
          </h2>

          {game.ideas.length === 0 ? (
            <EmptyState message="Nenhuma ideia extraída para esse jogo." />
          ) : (
            <div className="space-y-3">
              {game.ideas.map((idea) => (
                <IdeaCard key={idea.id} idea={idea} />
              ))}
            </div>
          )}
        </>
      )}
    </AppLayout>
  );
}
