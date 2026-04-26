"use client";

import { useState } from "react";
import AppLayout from "../../components/AppLayout";
import Card from "../../components/Card";
import Badge from "../../components/Badge";
import LoadingSpinner from "../../components/LoadingSpinner";
import { useApi } from "../../hooks/useApi";
import { fetchPendingIdeas, reviewIdea } from "../../services/ideas";
import type { Idea } from "../../services/ideas";

function IdeaReviewCard({ idea, onReviewed }: { idea: Idea; onReviewed: () => void }) {
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
    <Card className="p-5">
      <div className="flex flex-wrap gap-1.5 mb-4">
        <Badge label={idea.idea_type.replace(/_/g, " ")} color="indigo" />
        <Badge label={idea.market_type.replace(/_/g, " ")} color="blue" />
        <Badge label={`${Math.round(idea.extraction_confidence * 100)}% confiança`} color="yellow" />
      </div>

      <div className="space-y-1.5 text-sm mb-4">
        {idea.belief_text && (
          <p><span className="text-xs font-semibold text-slate-500 uppercase">Acredita</span><br />
            <span className="text-slate-800">{idea.belief_text}</span></p>
        )}
        {idea.fear_text && (
          <p><span className="text-xs font-semibold text-slate-500 uppercase">Teme</span><br />
            <span className="text-slate-800">{idea.fear_text}</span></p>
        )}
        {idea.entry_text && (
          <p><span className="text-xs font-semibold text-emerald-600 uppercase">Entrada</span><br />
            <span className="text-emerald-800">{idea.entry_text}</span></p>
        )}
      </div>

      {idea.source_excerpt && (
        <blockquote className="pl-3 border-l-2 border-slate-200 text-xs text-slate-400 italic mb-4">
          {idea.source_excerpt}
        </blockquote>
      )}

      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Notas de revisão (opcional)"
        className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-3"
        rows={2}
      />

      {error && <p className="text-xs text-red-600 mb-2">{error}</p>}

      <div className="flex gap-2">
        <button onClick={() => handle("approve")} disabled={submitting}
          className="flex-1 bg-emerald-600 text-white text-sm rounded-lg py-2 hover:bg-emerald-700 disabled:opacity-50">
          Aprovar
        </button>
        <button onClick={() => handle("reject")} disabled={submitting}
          className="flex-1 bg-red-500 text-white text-sm rounded-lg py-2 hover:bg-red-600 disabled:opacity-50">
          Rejeitar
        </button>
      </div>
    </Card>
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
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Revisão Humana</h1>
          <p className="text-sm text-slate-500 mt-0.5">Ideias com baixa confiança aguardando revisão.</p>
        </div>
        {!loading && (
          <span className="text-sm text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
            {pending.length} pendente{pending.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {!loading && !error && pending.length === 0 && (
        <Card className="p-10 text-center">
          <p className="text-2xl mb-2">✓</p>
          <p className="text-slate-500 text-sm font-medium">Tudo em ordem!</p>
          <p className="text-slate-400 text-xs mt-1">Nenhuma ideia pendente de revisão.</p>
        </Card>
      )}

      <div className="space-y-4">
        {pending.map((idea) => (
          <IdeaReviewCard key={idea.id} idea={idea} onReviewed={() => markReviewed(idea.id)} />
        ))}
      </div>

      {!loading && reviewed.size > 0 && (
        <div className="mt-6 text-center">
          <button onClick={() => { setReviewed(new Set()); refetch(); }}
            className="text-sm text-indigo-600 hover:underline">
            Recarregar fila de revisão
          </button>
        </div>
      )}
    </AppLayout>
  );
}
