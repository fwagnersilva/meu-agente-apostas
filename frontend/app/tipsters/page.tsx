"use client";

import { useState } from "react";
import Link from "next/link";
import AppLayout from "../../components/AppLayout";
import Card from "../../components/Card";
import Badge from "../../components/Badge";
import LoadingSpinner from "../../components/LoadingSpinner";
import { useApi } from "../../hooks/useApi";
import { fetchTipsters, createTipster } from "../../services/tipsters";

function CreateTipsterModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createTipster({ name: name.trim(), display_name: displayName.trim() || undefined, bio: bio.trim() || undefined });
      onCreated();
      onClose();
    } catch {
      setError("Erro ao criar tipster. Verifique se o nome já existe.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-5">Novo Tipster</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Nome interno *</label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="ex: casimiro_apostas"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Nome exibido</label>
            <input
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              placeholder="ex: Casimiro Apostas"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Bio</label>
            <textarea
              value={bio}
              onChange={e => setBio(e.target.value)}
              placeholder="Descrição do tipster..."
              rows={2}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 border border-slate-200 text-slate-600 text-sm rounded-lg py-2 hover:bg-slate-50">
              Cancelar
            </button>
            <button type="submit" disabled={submitting || !name.trim()}
              className="flex-1 bg-indigo-600 text-white text-sm rounded-lg py-2 hover:bg-indigo-700 disabled:opacity-50">
              {submitting ? "Criando..." : "Criar tipster"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TipstersPage() {
  const { data: tipsters, loading, error, refetch } = useApi(() => fetchTipsters(), []);
  const [showCreate, setShowCreate] = useState(false);

  return (
    <AppLayout>
      {showCreate && (
        <CreateTipsterModal onClose={() => setShowCreate(false)} onCreated={refetch} />
      )}

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Tipsters</h1>
          <p className="text-sm text-slate-500 mt-0.5">Criadores de conteúdo monitorados.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/tipsters/comparativo"
            className="px-3 py-1.5 border border-slate-200 text-slate-600 text-sm rounded-lg hover:bg-slate-50">
            Comparativo
          </Link>
          <button onClick={() => setShowCreate(true)}
            className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
            + Novo tipster
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner />}
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {!loading && !error && (tipsters ?? []).length === 0 && (
        <Card className="p-10 text-center">
          <p className="text-slate-400 text-sm">Nenhum tipster cadastrado ainda.</p>
          <button onClick={() => setShowCreate(true)} className="mt-3 text-indigo-600 text-sm hover:underline">
            Criar o primeiro tipster →
          </button>
        </Card>
      )}

      {!loading && !error && (tipsters ?? []).length > 0 && (
        <Card>
          <div className="divide-y divide-slate-100">
            {(tipsters ?? []).map((t) => (
              <Link key={t.id} href={`/tipsters/${t.id}`}
                className="flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition-colors">
                <div>
                  <p className="text-sm font-medium text-slate-800">{t.display_name ?? t.name}</p>
                  {t.bio && <p className="text-xs text-slate-400 mt-0.5 truncate max-w-sm">{t.bio}</p>}
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-xs text-slate-500">{t.channels_count} canal{t.channels_count !== 1 ? "is" : ""}</p>
                    <p className="text-xs text-slate-400">{t.actionable_ideas_count} acionáveis</p>
                  </div>
                  <Badge label={t.status === "active" ? "ativo" : "inativo"} color={t.status === "active" ? "green" : "gray"} />
                </div>
              </Link>
            ))}
          </div>
        </Card>
      )}
    </AppLayout>
  );
}
