"use client";

import { useState } from "react";
import AppLayout from "../../components/AppLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import EmptyState from "../../components/EmptyState";
import Badge from "../../components/Badge";
import { useApi } from "../../hooks/useApi";
import { fetchPendingIdeas, reviewIdea } from "../../services/ideas";
import type { Idea } from "../../services/ideas";

function IdeaReviewCard({
  idea,
  onReviewed,
}: {
  idea: Idea;
  onReviewed: () => void;
}) {
  const [submitting, setSubmitting] = useState(false);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handle(action: string) {
    setSubmitting(true);
    setError(null);
    try {
      await reviewIdea(idea.id, { action_type: action, notes: notes || undefined });
      onReviewed();
    } catch {
      setError("Erro ao salvar revisão.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex flex-wrap gap-1.5 mb-3">
        <Badge label={idea.idea_type.replace(/_/g, " ")} color="indigo" />
        <Badge label={idea.market_type.replace(/_/g, " ")} color="blue" />
        <Badge label={`${Math.round(idea.extraction_confidence * 100)}% confiança`} color="yellow" />
      </div>

      <div className="space-y-1 text-sm mb-3">
        {idea.belief_text && (
          <p>
            <span className="font-medium text-gray-600">Acredita: </span>
            <span className="text-gray-800">{idea.belief_text}</span>
          </p>
        )}
        {idea.fear_text && (
          <p>
            <span className="font-medium text-gray-600">Teme: </span>
            <span className="text-gray-800">{idea.fear_text}</span>
          </p>
        )}
        {idea.entry_text && (
          <p>
            <span className="font-medium text-green-700">Entrada: </span>
            <span className="text-green-800">{idea.entry_text}</span>
          </p>
        )}
      </div>

      {idea.source_excerpt && (
        <blockquote className="pl-3 border-l-2 border-gray-300 text-xs text-gray-500 italic mb-3">
          {idea.source_excerpt}
        </blockquote>
      )}

      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Notas de revisão (opcional)"
        className="w-full text-sm border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-3"
        rows={2}
      />

      {error && <p className="text-red-500 text-xs mb-2">{error}</p>}

      <div className="flex gap-2">
        <button
          onClick={() => handle("approve")}
          disabled={submitting}
          className="flex-1 bg-green-600 text-white text-sm rounded py-1.5 hover:bg-green-700 disabled:opacity-50"
        >
          Aprovar
        </button>
        <button
          onClick={() => handle("reject")}
          disabled={submitting}
          className="flex-1 bg-red-600 text-white text-sm rounded py-1.5 hover:bg-red-700 disabled:opacity-50"
        >
          Rejeitar
        </button>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  const { data: ideas, loading, error, refetch } = useApi(() => fetchPendingIdeas(), []);
  const [reviewed, setReviewed] = useState<Set<number>>(new Set());

  function markReviewed(id: number) {
    setReviewed((prev) => new Set([...prev, id]));
  }

  const pending = (ideas ?? []).filter((i) => !reviewed.has(i.id));

  return (
    <AppLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Revisão Humana</h1>
          <p className="text-sm text-gray-500 mt-1">
            Ideias com baixa confiança ou ambiguidade aguardando revisão.
          </p>
        </div>
        {!loading && (
          <span className="text-sm text-gray-500">
            {pending.length} pendente{pending.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {!loading && !error && pending.length === 0 && (
        <EmptyState message="Nenhuma ideia pendente de revisão. Tudo em ordem!" />
      )}

      <div className="space-y-4">
        {pending.map((idea) => (
          <IdeaReviewCard
            key={idea.id}
            idea={idea}
            onReviewed={() => markReviewed(idea.id)}
          />
        ))}
      </div>

      {!loading && reviewed.size > 0 && (
        <div className="mt-6 text-center">
          <button
            onClick={() => { setReviewed(new Set()); refetch(); }}
            className="text-sm text-indigo-600 hover:underline"
          >
            Recarregar fila de revisão
          </button>
        </div>
      )}
    </AppLayout>
  );
}
