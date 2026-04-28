import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CalendarDays, ChevronLeft, ChevronRight, Flame, Loader2,
  Pencil, Check, X, TrendingUp, Info, AlertTriangle,
} from "lucide-react";
import { useState } from "react";
import { fetchGames, upsertGameResult } from "@/services/games";
import type { Game, Idea } from "@/services/games";

// ── Labels legíveis ───────────────────────────────────────────────────────────

const MARKET_LABEL: Record<string, string> = {
  over_0_5: "Over 0.5", over_1_5: "Over 1.5", over_2_5: "Over 2.5", over_3_5: "Over 3.5",
  under_2_5: "Under 2.5", under_1_5: "Under 1.5",
  btts_yes: "Ambas marcam", btts_no: "Nenhuma marca",
  home_win: "Vitória casa", away_win: "Vitória fora", draw: "Empate",
  draw_no_bet: "Empate anula", asian_handicap: "Handicap asiático",
  double_chance: "Dupla chance",
  corners: "Escanteios", cards: "Cartões", player_props: "Props jogador",
  lay: "Lay", back: "Back", "1x2": "Resultado",
};

// idea_types que são apostas concretas (têm mercado ou intenção direta)
const BET_TYPES = new Set([
  "strong_entry", "possible_entry", "condition_based_entry",
  "watch_live", "no_value", "avoid_game",
]);

// idea_types que são contexto/análise (sem mercado direto)
const CONTEXT_TYPES = new Set([
  "risk_alert", "trend_read", "game_script", "caution", "contextual_note",
]);

const CONTEXT_LABEL: Record<string, string> = {
  risk_alert: "Alerta de risco",
  trend_read: "Tendência",
  game_script: "Script do jogo",
  caution: "Cautela",
  contextual_note: "Observação",
};

const NO_MARKET = new Set(["no_specific_market", "NO_SPECIFIC_MARKET", "", null, undefined]);

// ── Helpers ───────────────────────────────────────────────────────────────────

type TipsterInfo = { id: number; name: string };

function initials(name: string) {
  return name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
}

function TipsterBadge({ tipsters }: { tipsters: TipsterInfo[] }) {
  return (
    <span className="flex -space-x-1.5">
      {tipsters.map((t) => (
        <span
          key={t.id}
          title={t.name}
          className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-background bg-primary/20 text-[9px] font-bold text-primary cursor-default select-none"
        >
          {initials(t.name)}
        </span>
      ))}
    </span>
  );
}

function tipsterList(tipsters: Map<number, string>): TipsterInfo[] {
  return Array.from(tipsters.entries()).map(([id, name]) => ({ id, name }));
}

// ── Blocos de apostas e contexto ─────────────────────────────────────────────

interface BetEntry {
  key: string;
  label: string;
  tipsters: Map<number, string>;
  count: number;
  sentiment: "buy" | "avoid" | "watch" | "neutral";
}

interface ContextEntry {
  key: string;
  label: string; // texto da belief_text ou rationale_text truncado
  tipsters: Map<number, string>;
  idea_type: string;
}

function buildBets(ideas: Idea[]): BetEntry[] {
  const map = new Map<string, BetEntry>();

  for (const idea of ideas) {
    const hasMarket = !NO_MARKET.has(idea.market_type as string);
    // Só entra na seção apostas se tem mercado real OU é tipo aposta
    if (!hasMarket && CONTEXT_TYPES.has(idea.idea_type)) continue;

    const key = hasMarket ? idea.market_type : `__${idea.idea_type}__${idea.tipster_id}`;
    const label = hasMarket
      ? (idea.selection_label || MARKET_LABEL[idea.market_type] || idea.market_type)
      : (idea.belief_text?.slice(0, 60) || idea.idea_type);

    const sentiment: BetEntry["sentiment"] =
      idea.idea_type === "avoid_game" || idea.idea_type === "no_value" ? "avoid"
        : idea.idea_type === "watch_live" ? "watch"
          : idea.sentiment_direction === "favorable" ? "buy"
            : "neutral";

    if (!map.has(key)) {
      map.set(key, { key, label, tipsters: new Map(), count: 0, sentiment });
    }
    const entry = map.get(key)!;
    entry.count++;
    if (idea.tipster_id && idea.tipster_name) entry.tipsters.set(idea.tipster_id, idea.tipster_name);
    // Se mesmo mercado aparece com sentimentos opostos, prevalece "watch"
    if (entry.sentiment !== sentiment && hasMarket) entry.sentiment = "watch";
  }

  return Array.from(map.values()).sort((a, b) => b.count - a.count);
}

function buildContext(ideas: Idea[]): ContextEntry[] {
  // Pega apenas tipos contextuais, um por combinação tipster+tipo
  const seen = new Map<string, ContextEntry>();
  for (const idea of ideas) {
    if (!CONTEXT_TYPES.has(idea.idea_type)) continue;
    const text = idea.belief_text || idea.rationale_text || idea.entry_text || "";
    if (!text) continue;
    const key = `${idea.idea_type}__${idea.tipster_id}`;
    if (!seen.has(key)) {
      seen.set(key, {
        key,
        label: text.slice(0, 90) + (text.length > 90 ? "…" : ""),
        tipsters: new Map(),
        idea_type: idea.idea_type,
      });
    }
    if (idea.tipster_id && idea.tipster_name) {
      seen.get(key)!.tipsters.set(idea.tipster_id, idea.tipster_name);
    }
  }
  return Array.from(seen.values());
}

const SENTIMENT_STYLE: Record<BetEntry["sentiment"], string> = {
  buy: "border-success/40 bg-success/5 text-success",
  avoid: "border-destructive/40 bg-destructive/5 text-destructive",
  watch: "border-warning/40 bg-warning/5 text-warning",
  neutral: "border-border/50 bg-background/20 text-foreground",
};

const SENTIMENT_DOT: Record<BetEntry["sentiment"], string> = {
  buy: "bg-success",
  avoid: "bg-destructive",
  watch: "bg-warning",
  neutral: "bg-muted-foreground",
};

// ── IdeaSummary ───────────────────────────────────────────────────────────────

function IdeaSummary({ gameId, ideas }: { gameId: number; ideas: Idea[] }) {
  const bets = buildBets(ideas);
  const context = buildContext(ideas);

  if (bets.length === 0 && context.length === 0) return null;

  return (
    <div className="border-t border-border divide-y divide-border/40">

      {/* Bloco 1 — Apostas */}
      {bets.length > 0 && (
        <div className="px-3 py-2 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
            <TrendingUp className="h-3 w-3" /> Apostas
          </div>
          {bets.slice(0, 4).map((b) => (
            <div
              key={b.key}
              className={`flex items-center gap-2 rounded border px-2.5 py-1.5 text-xs ${SENTIMENT_STYLE[b.sentiment]}`}
            >
              <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${SENTIMENT_DOT[b.sentiment]}`} />
              <span className="font-medium flex-1 min-w-0 truncate">{b.label}</span>
              {b.count > 1 && (
                <span className="text-[10px] opacity-70 flex-shrink-0">{b.count}×</span>
              )}
              <TipsterBadge tipsters={tipsterList(b.tipsters)} />
            </div>
          ))}
          {bets.length > 4 && (
            <Link
              to="/jogos/$gameId"
              params={{ gameId: String(gameId) }}
              className="block text-[10px] text-primary hover:underline text-right"
            >
              +{bets.length - 4} apostas →
            </Link>
          )}
        </div>
      )}

      {/* Bloco 2 — Contexto */}
      {context.length > 0 && (
        <div className="px-3 py-2 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground mb-1.5">
            <Info className="h-3 w-3" /> Contexto dos tipsters
          </div>
          {context.slice(0, 3).map((c) => (
            <div key={c.key} className="flex items-start gap-2 rounded border border-border/40 bg-background/10 px-2.5 py-1.5 text-xs">
              {c.idea_type === "risk_alert" && (
                <AlertTriangle className="h-3 w-3 flex-shrink-0 mt-0.5 text-warning" />
              )}
              <span className="flex-1 text-muted-foreground leading-snug">{c.label}</span>
              <TipsterBadge tipsters={tipsterList(c.tipsters)} />
            </div>
          ))}
          {context.length > 3 && (
            <Link
              to="/jogos/$gameId"
              params={{ gameId: String(gameId) }}
              className="block text-[10px] text-primary hover:underline text-right"
            >
              +{context.length - 3} observações →
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

// ── ScoreEditor ───────────────────────────────────────────────────────────────

function ScoreEditor({ game }: { game: Game }) {
  const hasResult = game.result?.home_score != null;
  const [editing, setEditing] = useState(false);
  const [home, setHome] = useState(String(game.result?.home_score ?? ""));
  const [away, setAway] = useState(String(game.result?.away_score ?? ""));
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => upsertGameResult(game.id, Number(home), Number(away)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["games"] });
      setEditing(false);
    },
  });

  if (!editing) {
    return (
      <button
        onClick={() => setEditing(true)}
        className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        title={hasResult ? "Editar placar" : "Inserir placar final"}
      >
        {hasResult ? (
          <>
            <span className="font-mono font-semibold text-foreground">
              {game.result!.home_score} – {game.result!.away_score}
            </span>
            <Pencil className="h-3 w-3 ml-0.5 opacity-50" />
          </>
        ) : (
          <>
            <Pencil className="h-3 w-3" /> Placar
          </>
        )}
      </button>
    );
  }

  return (
    <span className="inline-flex items-center gap-1">
      <input
        type="number" min={0} max={99} value={home}
        onChange={e => setHome(e.target.value)}
        className="w-10 rounded border border-input bg-input/60 px-1.5 py-0.5 text-center text-xs font-mono outline-none focus:border-primary"
      />
      <span className="text-muted-foreground text-xs">–</span>
      <input
        type="number" min={0} max={99} value={away}
        onChange={e => setAway(e.target.value)}
        className="w-10 rounded border border-input bg-input/60 px-1.5 py-0.5 text-center text-xs font-mono outline-none focus:border-primary"
      />
      <button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending || home === "" || away === ""}
        className="rounded bg-primary/20 p-0.5 text-primary hover:bg-primary/30 disabled:opacity-50"
      >
        <Check className="h-3.5 w-3.5" />
      </button>
      <button onClick={() => setEditing(false)} className="rounded bg-muted p-0.5 text-muted-foreground hover:text-foreground">
        <X className="h-3.5 w-3.5" />
      </button>
    </span>
  );
}

// ── GameCard ──────────────────────────────────────────────────────────────────

function GameCard({ game }: { game: Game }) {
  const home = game.home_team?.name ?? "Time A";
  const away = game.away_team?.name ?? "Time B";

  return (
    <article className="rounded-lg border border-border bg-card overflow-hidden shadow-card hover:border-primary/30 transition-colors">
      {/* Status bar mínima */}
      <div className="flex items-center gap-2 px-3 py-1 bg-background/30 border-b border-border/60">
        {game.status === "live" && (
          <span className="inline-flex items-center gap-1 rounded-full bg-destructive/15 border border-destructive/30 px-1.5 py-0.5 text-[9px] font-bold uppercase text-destructive">
            <span className="h-1.5 w-1.5 rounded-full bg-destructive animate-pulse" /> Ao vivo
          </span>
        )}
        {game.status === "finished" && (
          <span className="rounded-full bg-muted px-1.5 py-0.5 text-[9px] font-medium uppercase text-muted-foreground">
            Encerrado
          </span>
        )}
        <span className="ml-auto flex items-center gap-1 text-[10px] text-primary font-medium">
          <Flame className="h-3 w-3" /> {game.ideas.length} ideias
        </span>
      </div>

      {/* Times + placar */}
      <Link
        to="/jogos/$gameId"
        params={{ gameId: String(game.id) }}
        className="grid grid-cols-[1fr_auto_1fr] items-center gap-1 px-3 py-2.5 hover:bg-accent/20 transition-colors"
      >
        <div className="text-right">
          <div className="text-sm font-semibold leading-tight">{home}</div>
        </div>
        <div className="text-center font-mono text-xs text-muted-foreground px-1">vs</div>
        <div>
          <div className="text-sm font-semibold leading-tight">{away}</div>
        </div>
      </Link>

      <div className="flex items-center justify-end px-3 pb-1">
        <ScoreEditor game={game} />
      </div>

      {game.ideas.length > 0 && <IdeaSummary gameId={game.id} ideas={game.ideas} />}
    </article>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export const Route = createFileRoute("/diario")({
  component: DiarioPage,
});

function offsetDate(base: string, days: number): string {
  const d = new Date(base + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().split("T")[0];
}

function DiarioPage() {
  const todayIso = new Date().toISOString().split("T")[0];
  const [selectedDate, setSelectedDate] = useState(todayIso);

  const dateLabel = new Date(selectedDate + "T12:00:00Z").toLocaleDateString("pt-BR", {
    weekday: "long", day: "numeric", month: "long",
  });

  const { data: games, isLoading } = useQuery({
    queryKey: ["games", selectedDate],
    queryFn: () => fetchGames(selectedDate),
  });

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-6 space-y-4">
      <div>
        <div className="flex items-center gap-2 text-xs uppercase tracking-widest text-primary">
          <CalendarDays className="h-3.5 w-3.5" /> Diário de jogos
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <button
            onClick={() => setSelectedDate(d => offsetDate(d, -1))}
            className="grid h-7 w-7 place-items-center rounded border border-border hover:border-primary/40 hover:text-primary transition-colors"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </button>
          <h1 className="text-xl font-bold capitalize">{dateLabel}</h1>
          <button
            onClick={() => setSelectedDate(d => offsetDate(d, +1))}
            className="grid h-7 w-7 place-items-center rounded border border-border hover:border-primary/40 hover:text-primary transition-colors"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => e.target.value && setSelectedDate(e.target.value)}
            className="rounded border border-input bg-input/40 px-2 py-1 text-xs outline-none focus:border-primary"
          />
          {selectedDate !== todayIso && (
            <button onClick={() => setSelectedDate(todayIso)} className="text-xs text-primary hover:underline">
              Hoje
            </button>
          )}
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {isLoading ? "Carregando…" : `${games?.length ?? 0} jogos`}
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-10">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
        </div>
      )}

      {!isLoading && (!games || games.length === 0) && (
        <div className="rounded-xl border border-border bg-card p-10 text-center">
          <CalendarDays className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">Nenhum jogo para este dia.</p>
          <p className="text-xs text-muted-foreground mt-1">
            Analise uma transcrição em{" "}
            <Link to="/videos" className="text-primary hover:underline">Vídeos</Link>.
          </p>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {games?.map((g) => <GameCard key={g.id} game={g} />)}
      </div>
    </div>
  );
}
