"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import AppLayout from "../../../components/AppLayout";
import Card from "../../../components/Card";
import Badge from "../../../components/Badge";
import LoadingSpinner from "../../../components/LoadingSpinner";
import { useApi } from "../../../hooks/useApi";
import { fetchTipster } from "../../../services/tipsters";
import { createChannel } from "../../../services/channels";

function AddChannelModal({ tipsterId, onClose, onCreated }: { tipsterId: number; onClose: () => void; onCreated: () => void }) {
  const [youtubeChannelId, setYoutubeChannelId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const id = youtubeChannelId.trim();
    if (!id) return;
    setSubmitting(true);
    setError(null);
    try {
      await createChannel({ tipster_id: tipsterId, platform: "youtube", platform_channel_id: id });
      onCreated();
      onClose();
    } catch {
      setError("Erro ao adicionar canal. Verifique o ID e tente novamente.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-2">Adicionar canal do YouTube</h2>
        <p className="text-xs text-slate-500 mb-5">
          Cole o ID do canal (ex: <code className="bg-slate-100 px-1 rounded">UCxxxxxxxxxxxxxxxxxxxxxx</code>) ou a URL completa do canal.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">ID ou URL do canal *</label>
            <input
              value={youtubeChannelId}
              onChange={e => setYoutubeChannelId(e.target.value)}
              placeholder="UCxxxxxx... ou youtube.com/channel/..."
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 border border-slate-200 text-slate-600 text-sm rounded-lg py-2 hover:bg-slate-50">
              Cancelar
            </button>
            <button type="submit" disabled={submitting || !youtubeChannelId.trim()}
              className="flex-1 bg-indigo-600 text-white text-sm rounded-lg py-2 hover:bg-indigo-700 disabled:opacity-50">
              {submitting ? "Adicionando..." : "Adicionar canal"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TipsterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: tipster, loading, error, refetch } = useApi(() => fetchTipster(Number(id)), [id]);
  const [showChannel, setShowChannel] = useState(false);

  return (
    <AppLayout>
      {showChannel && tipster && (
        <AddChannelModal tipsterId={tipster.id} onClose={() => setShowChannel(false)} onCreated={refetch} />
      )}

      <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-6">
        <Link href="/tipsters" className="text-indigo-600 hover:underline">Tipsters</Link>
        <span>/</span>
        <span>{tipster?.display_name ?? tipster?.name ?? "..."}</span>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {tipster && (
        <>
          <Card className="p-6 mb-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-xl font-semibold text-slate-900">{tipster.display_name ?? tipster.name}</h1>
                {tipster.bio && <p className="text-sm text-slate-500 mt-1 max-w-xl">{tipster.bio}</p>}
              </div>
              <div className="flex items-center gap-2">
                <Badge label={tipster.status === "active" ? "ativo" : "inativo"} color={tipster.status === "active" ? "green" : "gray"} />
                <button onClick={() => setShowChannel(true)}
                  className="px-3 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700">
                  + Canal
                </button>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-3 gap-4 mb-6">
            {[
              { label: "Canais", value: tipster.channels_count },
              { label: "Ideias totais", value: tipster.ideas_count },
              { label: "Acionáveis", value: tipster.actionable_ideas_count },
            ].map(({ label, value }) => (
              <Card key={label} className="p-4 text-center">
                <p className="text-2xl font-bold text-slate-900">{value}</p>
                <p className="text-xs text-slate-500 mt-1">{label}</p>
              </Card>
            ))}
          </div>
        </>
      )}
    </AppLayout>
  );
}
