import { useCallback, useEffect, useRef, useState } from "react";
import type { DragEvent, PointerEvent as ReactPointerEvent } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  Brain,
  Layers3,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Radio,
  Check,
  X,
  ScanLine,
  Download,
  Maximize,
  Pencil,
  MousePointer2,
  Users,
  ChevronRight,
  FileText,
  Circle,
  ShieldCheck,
  Command,
  MoveUpRight,
  Activity,
  GripVertical,
  VolumeX,
  Monitor,
  ExternalLink,
} from "lucide-react";
import type { Group, Memory, Trace, Document } from "./types";

const phases = ["Découvrir", "Se souvenir", "Montrer", "Déléguer", "Restituer"];
const timings = [
  "00–08 min",
  "08–28 min",
  "28–48 min",
  "48–78 min",
  "78–90 min",
];
const goalDefault =
  "Prépare une nouvelle implantation HORIZON pour 120 visiteurs. Respecte les contraintes d'accessibilité et un budget maximal de 6 000 €. Réorganise les ressources, prépare le planning et les communications. Soumets-moi les décisions importantes.";
const money = (n: number) => new Intl.NumberFormat("fr-FR").format(n) + " €";
async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const r = await fetch("/api" + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(
      typeof body.detail === "string" ? body.detail : "Requête invalide",
    );
  }
  return r.json();
}
const post = (body: unknown): RequestInit => ({
  method: "POST",
  body: JSON.stringify(body),
});

function Brand() {
  return (
    <a className="brand" href="/">
      WORK<span>/</span>2030<span className="brand-dot">✳</span>
    </a>
  );
}

export default function App() {
  const [groups, setGroups] = useState<{ id: string; name: string }[]>([]);
  const [error, setError] = useState("");
  const path = window.location.pathname;
  useEffect(() => {
    api<{ id: string; name: string }[]>("/sessions")
      .then(setGroups)
      .catch((e) => setError(e.message));
  }, []);
  if (path === "/animateur") return <Facilitator />;
  const sid = path.startsWith("/g/") ? path.slice(3) : null;
  if (sid) return <Workspace sid={sid} />;
  return (
    <div className="landing">
      <header>
        <Brand />
        <a className="text-link" href="/animateur">
          Poste animateur <ArrowUpRight size={16} />
        </a>
      </header>
      <main>
        <div className="eyebrow">
          <span className="live-dot" /> CRTHON 10 · LABORATOIRE D'INTERACTIONS
        </div>
        <h1>
          Le travail change.
          <br />
          <em>Votre environnement aussi.</em>
        </h1>
        <p className="landing-copy">
          Un lieu pour retrouver votre contexte, montrer une intention et faire
          travailler les outils ensemble. Bienvenue dans votre prochain poste de
          travail.
        </p>
        <div className="entry-heading">
          <span>CHOISISSEZ VOTRE TRINÔME</span>
          <span>01 — 05 / HORIZON</span>
        </div>
        <div className="group-grid">
          {groups.map((g, i) => (
            <a
              className="group-entry"
              key={g.id}
              href={"/g/" + g.id + window.location.search}
            >
              <span className="group-number">0{i + 1}</span>
              <div>
                <h3>{g.name}</h3>
                <p>
                  Entrer dans l'espace <ArrowUpRight size={15} />
                </p>
              </div>
              <div className="entry-orbit">✳</div>
            </a>
          ))}
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <div className="landing-bottom">
          <span>
            <VolumeX size={16} /> Sans micro. Sans compte. Données fictives.
          </span>
          <span>UNE EXPÉRIENCE À TROIS, AVEC L'ENVIRONNEMENT.</span>
        </div>
      </main>
      <footer>
        <span>WORK/2030 — EXPERIMENTAL WORKSPACE</span>
        <span>RETROUVER → MONTRER → DÉLÉGUER</span>
      </footer>
    </div>
  );
}

function Workspace({ sid }: { sid: string }) {
  const [group, setGroup] = useState<Group | null>(null);
  const [events, setEvents] = useState<Trace[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [found, setFound] = useState<Memory[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [zone, setZone] = useState("atelier");
  const [start, setStart] = useState("09:00");
  const [end, setEnd] = useState("12:00");
  const [goal, setGoal] = useState(goalDefault);
  const [provider, setProvider] = useState("demo");
  const [code, setCode] = useState(
    new URLSearchParams(window.location.search).get("card") ?? "",
  );
  const [mode, setMode] = useState<"select" | "draw">("select");
  const [points, setPoints] = useState<number[][]>([]);
  const [drawing, setDrawing] = useState(false);
  const [doc, setDoc] = useState<Document | null>(null);
  const [tab, setTab] = useState<"memory" | "resources">("memory");
  const [traceOpen, setTraceOpen] = useState(true);
  const [online, setOnline] = useState(true);
  const [pending, setPending] = useState(false);
  const refresh = useCallback(
    () => api<Group>("/sessions/" + sid).then(setGroup),
    [sid],
  );
  const run = useCallback(
    async (fn: () => Promise<unknown>, message = "") => {
      setPending(true);
      setError("");
      try {
        await fn();
        await refresh();
        if (message) setNotice(message);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setPending(false);
      }
    },
    [refresh],
  );
  const action = (name: string, data: unknown = {}) =>
    run(() =>
      api("/sessions/" + sid + "/actions", post({ action: name, data })),
    );
  useEffect(() => {
    let alive = true;
    refresh().catch((e) => setError(e.message));
    api<Trace[]>("/sessions/" + sid + "/events").then((e) => {
      if (alive) setEvents(e);
    });
    const es = new EventSource("/api/sessions/" + sid + "/stream");
    es.onmessage = (ev) => {
      const e = JSON.parse(ev.data) as Trace;
      setEvents((old) => (old.some((x) => x.id === e.id) ? old : [...old, e]));
      refresh().catch(() => setOnline(false));
    };
    es.onopen = () => setOnline(true);
    es.onerror = () => setOnline(false);
    const poll = window.setInterval(
      () => refresh().catch(() => setOnline(false)),
      2000,
    );
    return () => {
      alive = false;
      es.close();
      clearInterval(poll);
    };
  }, [sid, refresh]);
  useEffect(() => {
    if (!notice) return;
    const t = setTimeout(() => setNotice(""), 4000);
    return () => clearTimeout(t);
  }, [notice]);
  if (!group)
    return (
      <div className="loading">
        <Brand />
        <p role="alert">{error || "Connexion à votre environnement…"}</p>
        <a href="/">Retour aux groupes</a>
      </div>
    );
  const s = group.state;
  const space = s.spaces.find((x) => x.id === s.space_id)!;
  const phase = s.phase;
  const disabled = pending || group.active || s.paused;
  const p = s.proposal;
  const selectedResource = s.resources.find((r) => r.id === selected[0]);
  const addContext = (id: string) => action("context", { id, enabled: true });
  const dropContext = (e: DragEvent) => {
    e.preventDefault();
    const id = e.dataTransfer.getData("memory");
    if (id) addContext(id);
  };
  const toggleSelect = (id: string) =>
    setSelected((old) =>
      old.includes(id) ? old.filter((x) => x !== id) : [...old, id],
    );
  const prepare = (alternative = false) =>
    run(() =>
      api(
        "/sessions/" + sid + "/mission",
        post({
          goal,
          provider,
          alternative,
          focus: { resource_ids: selected, zone },
        }),
      ),
    );
  const pointer = (e: ReactPointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    return [
      Math.max(0, Math.min(100, ((e.clientX - r.left) / r.width) * 100)),
      Math.max(0, Math.min(100, ((e.clientY - r.top) / r.height) * 100)),
    ];
  };
  const saveDrawing = (e: ReactPointerEvent<SVGSVGElement>) => {
    if (drawing) {
      setDrawing(false);
      e.currentTarget.releasePointerCapture(e.pointerId);
      if (points.length > 1)
        action("annotate", { points, label: "Zone entourée par le pilote" });
      setPoints([]);
    }
  };
  const trace = events.filter(
    (e) =>
      e.kind.startsWith("tool.") ||
      e.kind.startsWith("decision.") ||
      e.kind.startsWith("mission.") ||
      e.kind.startsWith("model."),
  );
  const lastError = [...events]
    .reverse()
    .find((e) => e.kind === "mission.error");
  const roles = ["Pilote", "Copilote", "Superviseur"];
  return (
    <div className="workspace-shell">
      <header className="app-header">
        <Brand />
        <div className="header-project">
          <span className="project-tag">H</span>
          <div>
            <b>Mission HORIZON</b>
            <span>120 visiteurs · Ouverture dans 48 h</span>
          </div>
        </div>
        <div className="header-right">
          <span className="connection">
            <span className={"live-dot " + (!online ? "offline" : "")} />
            {online ? "Environnement connecté" : "Reconnexion…"}
          </span>
          <span className="group-pill">{group.name}</span>
          <button
            className="icon-button"
            aria-label="Plein écran"
            onClick={() =>
              run(async () => {
                if (document.fullscreenElement) await document.exitFullscreen();
                else await document.documentElement.requestFullscreen();
              })
            }
          >
            <Maximize size={17} />
          </button>
          <a className="icon-button" aria-label="Changer de groupe" href="/">
            <Users size={17} />
          </a>
        </div>
      </header>
      <nav className="phase-bar" aria-label="Séquences de l'atelier">
        {phases.map((title, i) => (
          <button
            key={title}
            className={
              "phase " + (phase === i ? "current" : phase > i ? "past" : "")
            }
            onClick={() => action("phase", { phase: i })}
            disabled={disabled}
          >
            <span className="phase-num">
              {phase > i ? <Check size={13} /> : String(i + 1).padStart(2, "0")}
            </span>
            <span>
              {title}
              <small>{timings[i]}</small>
            </span>
            {i < 4 && <ChevronRight className="phase-chevron" size={15} />}
          </button>
        ))}
        <div className="role-switch">
          <span>
            {roles[s.roles]} · {roles[(s.roles + 1) % 3]} ·{" "}
            {roles[(s.roles + 2) % 3]}
          </span>
          <button
            title="Faire tourner les rôles"
            aria-label="Faire tourner les rôles"
            disabled={disabled}
            onClick={() => action("roles")}
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </nav>
      {s.paused && (
        <div className="pause-banner">
          <Pause size={16} /> Session en pause par l'animateur. Votre
          environnement est conservé.
        </div>
      )}
      {(error || notice) && (
        <div
          className={error ? "toast error" : "toast success"}
          role={error ? "alert" : "status"}
        >
          {error || notice}
          <button
            aria-label="Fermer le message"
            onClick={() => {
              setError("");
              setNotice("");
            }}
          >
            <X size={16} />
          </button>
        </div>
      )}
      <main className="work-grid">
        <aside className="library">
          <div className="panel-label">
            01 / LES CONNAISSANCES <Layers3 size={14} />
          </div>
          <h2>
            Votre mémoire,
            <br />
            <span>à portée d'intention.</span>
          </h2>
          <div className="tabs">
            <button
              className={tab === "memory" ? "active" : ""}
              onClick={() => setTab("memory")}
            >
              <Brain size={14} /> Mémoire
            </button>
            <button
              className={tab === "resources" ? "active" : ""}
              onClick={() => setTab("resources")}
            >
              <Layers3 size={14} /> Ressources{" "}
              <small>{s.resources.length}</small>
            </button>
          </div>
          {tab === "memory" ? (
            <>
              <form
                className="search-box"
                onSubmit={(e) => {
                  e.preventDefault();
                  run(async () => {
                    const r = await api<{ items: Memory[] }>(
                      "/sessions/" +
                        sid +
                        "/memory?q=" +
                        encodeURIComponent(search),
                    );
                    setFound(r.items);
                  }, "Recherche effectuée dans les sources locales");
                }}
              >
                <input
                  aria-label="Rechercher dans la mémoire"
                  placeholder="Un souvenir, une contrainte…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <button aria-label="Rechercher" disabled={pending}>
                  <ArrowRight size={17} />
                </button>
              </form>
              <div className="suggestions">
                {["Accessibilité", "Équipement écarté", "Plan zone calme"].map(
                  (q) => (
                    <button
                      key={q}
                      onClick={() => {
                        setSearch(q);
                        run(async () => {
                          const r = await api<{ items: Memory[] }>(
                            "/sessions/" +
                              sid +
                              "/memory?q=" +
                              encodeURIComponent(q),
                          );
                          setFound(r.items);
                        });
                      }}
                    >
                      {q}
                    </button>
                  ),
                )}
              </div>
              <div className="library-caption">
                SOURCES LOCALES · {found?.length ?? s.memory.length} ÉLÉMENTS
                {found && (
                  <button
                    onClick={() => {
                      setFound(null);
                      setSearch("");
                    }}
                  >
                    Tout afficher
                  </button>
                )}
              </div>
              <div className="memory-list">
                {(found ?? s.memory).map((m) => (
                  <article
                    key={m.id}
                    className={
                      "memory-card " +
                      (m.superseded_by ? "outdated" : "") +
                      (s.context.includes(m.id) ? " in-context" : "")
                    }
                    draggable={!m.superseded_by && !disabled}
                    onDragStart={(e) => e.dataTransfer.setData("memory", m.id)}
                  >
                    <div className="memory-meta">
                      <span>
                        {m.visual
                          ? "PLAN VISUEL"
                          : m.id === "m-access"
                            ? "DÉCISION CONFIRMÉE"
                            : "SOURCE RETROUVÉE"}
                      </span>
                      <GripVertical size={13} />
                    </div>
                    <h3>{m.title}</h3>
                    {m.visual && <MiniPlan />}
                    <p>{m.text}</p>
                    <div className="memory-source">
                      <FileText size={12} />
                      {m.source}
                    </div>
                    <button
                      className="card-action"
                      disabled={
                        disabled ||
                        !!m.superseded_by ||
                        s.context.includes(m.id)
                      }
                      onClick={() => addContext(m.id)}
                    >
                      {m.superseded_by ? (
                        "Obsolète · remplacée"
                      ) : s.context.includes(m.id) ? (
                        <>
                          <Check size={13} /> Dans le contexte
                        </>
                      ) : (
                        <>
                          Ajouter au contexte <MoveUpRight size={14} />
                        </>
                      )}
                    </button>
                  </article>
                ))}
                {found?.length === 0 && (
                  <p className="empty">
                    Aucune source retrouvée. Essayez « calme » ou «
                    accessibilité ».
                  </p>
                )}
              </div>
              <p className="transparency">
                <ShieldCheck size={12} /> Sources retrouvées, sans inférence
                générative.
              </p>
            </>
          ) : (
            <>
              <p className="resource-instruction">
                Sélectionnez ou glissez un équipement vers une zone. Les
                contraintes sont vérifiées avant chaque affectation.
              </p>
              <div className="resource-list">
                {s.resources.map((r) => (
                  <button
                    key={r.id}
                    aria-pressed={selected.includes(r.id)}
                    className={
                      "resource-card " +
                      (selected.includes(r.id) ? "selected" : "") +
                      (!r.available ? " unavailable" : "")
                    }
                    draggable={r.available && !disabled}
                    onDragStart={(e) =>
                      e.dataTransfer.setData("resource", r.id)
                    }
                    onClick={() => toggleSelect(r.id)}
                  >
                    <span className="resource-icon">
                      {r.kind === "display" ? (
                        <Monitor size={17} />
                      ) : r.kind === "quiet" ? (
                        <Circle size={17} />
                      ) : (
                        <Layers3 size={17} />
                      )}
                    </span>
                    <span>
                      <b>{r.name}</b>
                      <small>
                        {!r.available
                          ? "Indisponible"
                          : s.assignments[r.id]
                            ? s.assignments[r.id].zone +
                              " · " +
                              s.assignments[r.id].start
                            : "Disponible · " + money(r.cost)}
                      </small>
                    </span>
                    <span className="resource-select">
                      {selected.includes(r.id) ? (
                        <Check size={13} />
                      ) : (
                        <GripVertical size={13} />
                      )}
                    </span>
                  </button>
                ))}
              </div>
              {selectedResource && (
                <div className="assign-editor">
                  <h3>{selected.length} ressource(s) sélectionnée(s)</h3>
                  <p>
                    Zones compatibles :{" "}
                    {selectedResource.allowed_zones.join(", ")}
                  </p>
                  <label>
                    Zone
                    <select
                      aria-label="Zone d'affectation"
                      value={zone}
                      onChange={(e) => setZone(e.target.value)}
                    >
                      {space.zones.map((z) => (
                        <option key={z.id} value={z.id}>
                          {z.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="time-inputs">
                    <label>
                      Début
                      <input
                        aria-label="Début du créneau"
                        type="time"
                        value={start}
                        onChange={(e) => setStart(e.target.value)}
                      />
                    </label>
                    <label>
                      Fin
                      <input
                        aria-label="Fin du créneau"
                        type="time"
                        value={end}
                        onChange={(e) => setEnd(e.target.value)}
                      />
                    </label>
                  </div>
                  <button
                    className="secondary-button"
                    disabled={disabled || selected.length !== 1}
                    onClick={() =>
                      action("assign", { id: selected[0], zone, start, end })
                    }
                  >
                    Affecter la ressource <ArrowRight size={14} />
                  </button>
                </div>
              )}
            </>
          )}
        </aside>
        <section className="center-work">
          <div className="workspace-heading">
            <div>
              <div className="eyebrow">ESPACE PARTAGÉ / HORIZON 2030</div>
              <h1>
                {phase === 0
                  ? "Et si votre poste travaillait avec vous ?"
                  : phase === 1
                    ? "Retrouver. Relier. Se souvenir."
                    : phase === 2
                      ? "Une fois pour vous. La suite ensemble."
                      : phase === 3
                        ? "Votre intention devient un espace."
                        : "Ce que vous avez rendu possible."}
              </h1>
            </div>
            <span className="live-label">
              <span className="live-dot" />{" "}
              {group.active ? "OUTILS EN ACTION" : "ESPACE VIVANT"}
            </span>
          </div>
          <div className="mission-strip">
            <span className="mission-icon">
              {phase === 1 ? (
                <Brain size={20} />
              ) : phase === 2 ? (
                <Command size={20} />
              ) : (
                <Sparkles size={20} />
              )}
            </span>
            <div>
              <b>
                {phase === 0
                  ? "Bienvenue dans le laboratoire"
                  : phase === 1
                    ? "Mission 01 · Le poste qui se souvient"
                    : phase === 2
                      ? "Mission 02 · Montre-lui une fois"
                      : phase === 3
                        ? "Mission 03 · Les outils travaillent"
                        : "Mission 04 · Comparer vos expériences"}
              </b>
              <p>
                {phase === 0
                  ? "Trois personnes. Trois rôles. Un environnement qui agit. Explorez le plan, puis ouvrez la mémoire."
                  : phase === 1
                    ? "Retrouvez la contrainte d’accessibilité, puis replacez sa source dans le contexte. Retirez-la pour observer la différence."
                    : phase === 2
                      ? "Enregistrez une affectation de l’îlot A, changez son horaire, puis reproduisez-la sur l’îlot B."
                      : phase === 3
                        ? "Préparez HORIZON. Observez les outils et validez les décisions avant leur exécution."
                        : "Exportez votre trace et discutez : que délégueriez-vous, et sous quelle supervision ?"}
              </p>
            </div>
          </div>
          <div
            className="canvas-container"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              const mid = e.dataTransfer.getData("memory");
              if (mid) {
                e.preventDefault();
                addContext(mid);
              }
            }}
          >
            <div className="canvas-top">
              <div>
                <span className="plan-symbol">⌑</span>
                <b>{space.name}</b>
                <span className="canvas-subtitle">PLAN D'IMPLANTATION</span>
              </div>
              <div className="canvas-tools">
                <button
                  className={mode === "select" ? "active" : ""}
                  aria-label="Sélectionner"
                  onClick={() => setMode("select")}
                >
                  <MousePointer2 size={16} />
                </button>
                <button
                  className={mode === "draw" ? "active" : ""}
                  aria-label="Entourer une zone"
                  onClick={() => setMode("draw")}
                >
                  <Pencil size={16} />
                </button>
                <button
                  aria-label="Annuler la dernière modification"
                  disabled={disabled}
                  onClick={() =>
                    run(
                      () => api("/sessions/" + sid + "/undo", post({})),
                      "État précédent restauré",
                    )
                  }
                >
                  <RotateCcw size={16} />
                </button>
              </div>
            </div>
            <div className="plan-wrap">
              <svg
                className={"plan " + (mode === "draw" ? "draw-mode" : "")}
                viewBox="0 0 1000 560"
                role="img"
                aria-label="Plan interactif des zones HORIZON"
                onPointerDown={(e) => {
                  if (mode === "draw" && !disabled) {
                    e.currentTarget.setPointerCapture(e.pointerId);
                    setDrawing(true);
                    setPoints([pointer(e)]);
                  }
                }}
                onPointerMove={(e) => {
                  if (drawing) {
                    const nextPoint = pointer(e);
                    setPoints((old) =>
                      old.length < 500 ? [...old, nextPoint] : old,
                    );
                  }
                }}
                onPointerUp={saveDrawing}
                onPointerCancel={() => {
                  setDrawing(false);
                  setPoints([]);
                }}
              >
                <defs>
                  <pattern
                    id="grid"
                    width="20"
                    height="20"
                    patternUnits="userSpaceOnUse"
                  >
                    <circle cx="1" cy="1" r=".8" fill="#344238" />
                  </pattern>
                  <pattern
                    id="quiet-grid"
                    width="16"
                    height="16"
                    patternUnits="userSpaceOnUse"
                  >
                    <path d="M0 16L16 0" stroke="#54735e" strokeWidth=".5" />
                  </pattern>
                </defs>
                <rect width="1000" height="560" fill="url(#grid)" />
                <path
                  d="M40 26H960V525H40Z"
                  fill="none"
                  stroke="#5b6d60"
                  strokeWidth="2"
                />
                <path d="M425 525H555" stroke="#121d17" strokeWidth="7" />
                <path
                  d="M470 540v-34m-10 13l10-13 10 13"
                  stroke="#b9df88"
                  fill="none"
                  strokeWidth="2"
                />
                <text
                  x="495"
                  y="550"
                  fill="#9dae9f"
                  fontSize="10"
                  letterSpacing="3"
                >
                  ENTRÉE
                </text>
                {space.zones.map((z, i) => {
                  const x = z.x * 10,
                    y = z.y * 5.6,
                    w = z.w * 10,
                    h = z.h * 5.6;
                  const objects = Object.entries(s.assignments).filter(
                    ([, a]) => a.zone === z.id,
                  );
                  return (
                    <g
                      key={z.id}
                      role="button"
                      tabIndex={0}
                      aria-label={"Zone " + z.name}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          setZone(z.id);
                          setTab("resources");
                        }
                      }}
                      onClick={() => {
                        if (mode === "select") {
                          setZone(z.id);
                          setTab("resources");
                        }
                      }}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const id = e.dataTransfer.getData("resource");
                        if (id)
                          action("assign", { id, zone: z.id, start, end });
                        const mid = e.dataTransfer.getData("memory");
                        if (mid) addContext(mid);
                      }}
                    >
                      <rect
                        x={x}
                        y={y}
                        width={w}
                        height={h}
                        rx="5"
                        fill={
                          z.id === "calme"
                            ? "#263a2b"
                            : z.id === "scene"
                              ? "#22322a"
                              : "#253329"
                        }
                        stroke={zone === z.id ? "#badb91" : "#657467"}
                        strokeWidth={zone === z.id ? 2 : 1}
                      />
                      {z.id === "calme" && (
                        <rect
                          x={x + 1}
                          y={y + 1}
                          width={w - 2}
                          height={h - 2}
                          fill="url(#quiet-grid)"
                        />
                      )}
                      <text
                        x={x + 20}
                        y={y + 29}
                        fill="#819685"
                        fontSize="10"
                        letterSpacing="3"
                      >
                        ZONE 0{i + 1}
                      </text>
                      <text x={x + 20} y={y + 56} fill="#e9eee4" fontSize="22">
                        {z.name}
                      </text>
                      <text x={x + 20} y={y + 77} fill="#9aaa9b" fontSize="12">
                        {z.capacity} places{" "}
                        {p?.status === "completed"
                          ? "· " + p.plan.occupancy[z.id] + " prévues"
                          : ""}
                      </text>
                      {z.id === "scene" && (
                        <g opacity=".6">
                          <rect
                            x={x + w - 155}
                            y={y + 25}
                            width="125"
                            height="28"
                            rx="3"
                            fill="#647f63"
                          />
                          <text
                            x={x + w - 135}
                            y={y + 44}
                            fill="#d6e4ce"
                            fontSize="10"
                            letterSpacing="2"
                          >
                            SCÈNE
                          </text>
                          {Array.from({ length: 24 }, (_, j) => (
                            <rect
                              key={j}
                              x={x + 40 + (j % 8) * 46}
                              y={y + 102 + Math.floor(j / 8) * 28}
                              width="20"
                              height="12"
                              rx="3"
                              fill="#4a5e4e"
                            />
                          ))}
                        </g>
                      )}
                      {z.id === "atelier" &&
                        [0, 1].map((j) => (
                          <g key={j} opacity=".45">
                            <rect
                              x={x + 65}
                              y={y + 105 + j * 120}
                              width="170"
                              height="75"
                              rx="30"
                              fill="#586c4f"
                            />
                            <circle
                              cx={x + 45}
                              cy={y + 145 + j * 120}
                              r="8"
                              fill="#9db180"
                            />
                            <circle
                              cx={x + 255}
                              cy={y + 145 + j * 120}
                              r="8"
                              fill="#9db180"
                            />
                          </g>
                        ))}
                      {z.id === "calme" &&
                        [0, 1, 2].map((j) => (
                          <rect
                            key={j}
                            x={x + 185 + j * 53}
                            y={y + 98}
                            width="32"
                            height="30"
                            rx="7"
                            fill="#759268"
                            opacity=".7"
                          />
                        ))}
                      {objects.map(([rid, a], j) => (
                        <g
                          key={rid}
                          role="button"
                          tabIndex={0}
                          aria-label={"Objet " + rid}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") toggleSelect(rid);
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleSelect(rid);
                            setTab("resources");
                          }}
                        >
                          <rect
                            x={x + 18}
                            y={y + h - 35 - j * 32}
                            width={Math.min(w - 36, 260)}
                            height="27"
                            rx="5"
                            fill={
                              selected.includes(rid) ? "#bce292" : "#3a4f3b"
                            }
                            stroke="#8bb37b"
                          />
                          <text
                            x={x + 28}
                            y={y + h - 17 - j * 32}
                            fill={
                              selected.includes(rid) ? "#17291c" : "#e6f2de"
                            }
                            fontSize="11"
                          >
                            {s.resources.find((r) => r.id === rid)?.name} ·{" "}
                            {a.start}
                          </text>
                        </g>
                      ))}
                    </g>
                  );
                })}
                <path
                  d="M560 298H620V490H475"
                  stroke="#a9d47c"
                  strokeWidth="2"
                  strokeDasharray="6 7"
                  opacity=".8"
                  fill="none"
                />
                <text
                  x="476"
                  y="320"
                  fill="#9bbf7e"
                  fontSize="9"
                  letterSpacing="1"
                >
                  CHEMINEMENT {space.aisle_cm} CM
                </text>
                {s.annotations.map((a) => (
                  <polyline
                    key={a.id}
                    points={a.points
                      .map((p) => `${p[0] * 10},${p[1] * 5.6}`)
                      .join(" ")}
                    fill="none"
                    stroke="#e8b873"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                ))}
                {points.length > 0 && (
                  <polyline
                    points={points
                      .map((p) => `${p[0] * 10},${p[1] * 5.6}`)
                      .join(" ")}
                    fill="none"
                    stroke="#e8b873"
                    strokeWidth="3"
                  />
                )}
              </svg>
            </div>
            <div className="canvas-bottom">
              <span>
                <span className="legend-dot" /> {space.capacity} places
                disponibles
              </span>
              <span>
                <ShieldCheck size={13} />{" "}
                {space.accessible ? "Accès sans marches" : "Accès à vérifier"}
              </span>
              <span>
                {mode === "draw"
                  ? "Tracez pour annoter le plan"
                  : "Glissez du matériel · sélectionnez une zone"}
              </span>
            </div>
          </div>
          <div
            className="context-tray"
            onDragOver={(e) => e.preventDefault()}
            onDrop={dropContext}
          >
            <div className="context-heading">
              <Brain size={17} />
              <b>Contexte actif</b>
              <span>
                {s.context.length} source{s.context.length > 1 ? "s" : ""}
              </span>
              <small>CE QUE L'ENVIRONNEMENT PREND EN COMPTE</small>
            </div>
            <div className="context-items">
              {s.context.length === 0 ? (
                <span className="context-empty">
                  Glissez une source ici, ou cliquez sur « Ajouter au contexte
                  ». La décision d'accessibilité manque encore.
                </span>
              ) : (
                s.context.map((id) => (
                  <span className="context-chip" key={id}>
                    <FileText size={13} />
                    {s.memory.find((m) => m.id === id)?.title}
                    <button
                      aria-label={"Retirer " + id}
                      disabled={disabled}
                      onClick={() => action("context", { id, enabled: false })}
                    >
                      <X size={13} />
                    </button>
                  </span>
                ))
              )}
            </div>
            <div className="context-summary">
              <span>
                Cheminement requis{" "}
                <b>{group.effective_constraints.aisle_cm} cm</b>
              </span>
              <span>
                Places calmes requises{" "}
                <b>{group.effective_constraints.quiet_places}</b>
              </span>
              <span>
                Budget <b>{money(group.effective_constraints.budget)}</b>
              </span>
            </div>
          </div>
          {phase === 2 && (
            <div className="learning-panel">
              <div>
                <div className="eyebrow">AUTOMATISATION SÉMANTIQUE INTERNE</div>
                <h3>
                  {s.recording
                    ? "Votre démonstration est en cours."
                    : s.recipe
                      ? "Une recette prête à être réutilisée."
                      : "Montrez une affectation à votre environnement."}
                </h3>
                <p>
                  {s.recording
                    ? `${s.recorded.length} action(s) enregistrée(s). Sélectionnez l'îlot A dans Ressources, affectez-le puis changez son horaire.`
                    : s.recipe
                      ? `Variable : resource_id · ${s.recipe.steps.length} étape(s) · ${s.recipe.zone}, ${s.recipe.start}–${s.recipe.end}. Sélectionnez l'îlot B pour reproduire.`
                      : "Cliquez sur Enregistrer, puis manipulez une seule ressource. Les contraintes sont contrôlées à chaque étape."}
                </p>
                {s.recorded.length > 0 && (
                  <div className="recorded-steps">
                    {s.recorded.map((a, i) => (
                      <span key={i}>
                        {i + 1}. {a.resource_id} → {a.zone} · {a.start}–{a.end}
                      </span>
                    ))}
                  </div>
                )}
                {s.last_replay && (
                  <p className="success-text">
                    Reproduction exécutée sur {s.last_replay.count}{" "}
                    ressource(s). Annulation disponible dans le plan.
                  </p>
                )}
              </div>
              <div className="learning-buttons">
                {s.recording ? (
                  <button
                    className="primary-button"
                    disabled={disabled}
                    onClick={() => action("record_finish")}
                  >
                    J'ai terminé <Check size={15} />
                  </button>
                ) : (
                  <button
                    className="secondary-button"
                    disabled={disabled}
                    onClick={() => {
                      setTab("resources");
                      action("record_start");
                    }}
                  >
                    <Circle size={14} /> Enregistrer
                  </button>
                )}
                {s.recipe && (
                  <button
                    className="primary-button"
                    disabled={disabled || selected.length === 0}
                    onClick={() => action("replay", { ids: selected })}
                  >
                    Fais-le pour moi <Play size={14} />
                  </button>
                )}
              </div>
            </div>
          )}
          <div className="deliverable-row">
            <div className="mini-budget">
              <span className="eyebrow">
                BUDGET {s.budget ? "ENGAGÉ" : "PRÉVISIONNEL"}
              </span>
              <strong>
                {s.budget
                  ? money(s.budget.total)
                  : p
                    ? money(p.budget.total)
                    : "—"}
                <small>/ {money(group.effective_constraints.budget)}</small>
              </strong>
              <div className="budget-bar">
                <i
                  style={{
                    width:
                      Math.min(
                        100,
                        ((s.budget?.total ?? p?.budget.total ?? 0) /
                          group.effective_constraints.budget) *
                          100,
                      ) + "%",
                  }}
                />
              </div>
            </div>
            <div className="deliverables">
              <div className="eyebrow">PRODUCTIONS DE L'ENVIRONNEMENT</div>
              {s.documents.length + s.messages.length === 0 ? (
                <p>
                  Le plan, le planning et les communications prendront forme
                  ici.
                </p>
              ) : (
                <div>
                  {[...s.documents, ...s.messages].map((d) => (
                    <button key={d.id} onClick={() => setDoc(d)}>
                      <FileText size={15} />
                      {d.title}
                      <ArrowUpRight size={13} />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          {s.schedule.length > 0 && (
            <div className="schedule">
              <span className="eyebrow">PLANNING GÉNÉRÉ</span>
              {s.schedule.map((e) => (
                <div key={e.id}>
                  <b>
                    {e.start}–{e.end}
                  </b>
                  <span>{e.name}</span>
                  <small>{e.zone}</small>
                </div>
              ))}
            </div>
          )}
          {phase === 4 && (
            <div className="debrief">
              <h3>
                Votre environnement a produit {s.documents.length} document(s),{" "}
                {s.messages.length} brouillon(s) et{" "}
                {s.assignments ? Object.keys(s.assignments).length : 0}{" "}
                affectations.
              </h3>
              <p>
                Comparez la trace des outils et les validations humaines. Où
                avez-vous gardé la main ? Où le contexte a-t-il changé le
                résultat ?
              </p>
              <a
                className="primary-button"
                href={"/api/sessions/" + sid + "/export"}
              >
                <Download size={16} /> Exporter le résumé et la trace
              </a>
            </div>
          )}
        </section>
        <aside className="agent-panel">
          <div className="panel-label">
            02 / L'ENVIRONNEMENT AGIT <Sparkles size={14} />
          </div>
          <div className="agent-heading">
            <div className={"agent-orb " + (group.active ? "working" : "")}>
              ✳
            </div>
            <div>
              <h2>À vos côtés.</h2>
              <span>
                {provider === "demo"
                  ? "Orchestration prédéfinie"
                  : "Conseil modèle + orchestration"}
              </span>
            </div>
            <span className="agent-status" />
          </div>
          <p className="agent-intro">
            Donnez le résultat souhaité.
            <br />
            Observez le chemin pour y arriver.
          </p>
          <label className="intent-label" htmlFor="goal">
            VOTRE INTENTION
          </label>
          <textarea
            id="goal"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            rows={5}
          />
          <div className="provider-select">
            <select
              aria-label="Mode d'orchestration"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
            >
              <option value="demo">Démo · sans clé API</option>
              <option value="openai">OpenAI · conseil de lieu</option>
              <option value="ollama">Ollama · conseil de lieu</option>
            </select>
            <ShieldCheck size={14} />
          </div>
          <p className="mode-note">
            {provider === "demo"
              ? "Scénario HORIZON prédéfini. Les contraintes actives pilotent réellement le choix. Le texte libre est conservé dans la trace."
              : "Le modèle choisit parmi les lieux admissibles via un appel d’outil. Les actions restent bornées et supervisées."}
          </p>
          <button
            className="primary-button intent-button"
            disabled={disabled}
            onClick={() => prepare()}
          >
            {group.active ? (
              <>
                <Activity size={16} /> Outils en cours…
              </>
            ) : (
              <>
                <Sparkles size={16} /> Préparer la mission{" "}
                <ArrowUpRight size={16} />
              </>
            )}
          </button>
          <p className="mode-note">
            Sélection visuelle :{" "}
            {selected.length
              ? selected.join(", ") + " → " + zone
              : "aucune ressource ciblée"}
            . Les affectations de la mission utiliseront cette sélection.
          </p>
          <details className="constraints-editor">
            <summary>
              Ajuster les contraintes <ChevronRight size={13} />
            </summary>
            {(
              [
                { key: "budget", label: "Budget maximal (€)" },
                { key: "visitors", label: "Visiteurs" },
                { key: "aisle_cm", label: "Passage (cm)" },
                { key: "quiet_places", label: "Places calmes" },
              ] as const
            ).map((c) => (
              <label key={c.key}>
                {c.label}
                <input
                  type="number"
                  aria-label={c.label}
                  key={s.constraints[c.key]}
                  defaultValue={s.constraints[c.key]}
                  disabled={disabled}
                  onBlur={(e) => {
                    const value = Number(e.target.value);
                    if (value !== s.constraints[c.key])
                      action("constraint", { key: c.key, value });
                  }}
                />
              </label>
            ))}
            <p>
              Les contraintes ci-dessus, la mémoire active et les disponibilités
              gouvernent le scénario.
            </p>
          </details>
          {s.perturbation && (
            <div className="perturbation">
              <Radio size={16} />
              <div>
                <b>Un imprévu vient d'arriver</b>
                <p>{s.perturbation}</p>
              </div>
            </div>
          )}
          {p && (
            <div
              className={
                "decision-card " + (p.status === "completed" ? "done" : "")
              }
            >
              <div className="decision-eyebrow">
                <ShieldCheck size={14} />
                {p.status === "pending"
                  ? "À VALIDER PAR LE SUPERVISEUR"
                  : p.status === "completed"
                    ? "DÉCISION EXÉCUTÉE"
                    : p.status === "rejected"
                      ? "PROPOSITION REFUSÉE"
                      : "EXÉCUTION EN COURS"}
              </div>
              <h3>{s.spaces.find((x) => x.id === p.plan.space_id)?.name}</h3>
              <p>{p.reason}</p>
              <div className="decision-stats">
                <span>{money(p.budget.total)}</span>
                <span>
                  {Object.values(p.plan.occupancy).reduce((a, b) => a + b, 0)}{" "}
                  visiteurs
                </span>
              </div>
              <details>
                <summary>Voir le budget et la répartition</summary>
                {p.budget.lines.map((l, i) => (
                  <div className="budget-line" key={i}>
                    <span>{l.name}</span>
                    <b>{money(l.amount)}</b>
                  </div>
                ))}
                {Object.entries(p.plan.occupancy).map(([z, n]) => (
                  <div className="budget-line" key={z}>
                    <span>{z}</span>
                    <b>{n} places</b>
                  </div>
                ))}
              </details>
              {p.warnings.map((w) => (
                <p className="critic" key={w}>
                  <ScanLine size={14} />
                  {w}
                </p>
              ))}
              {group.proposal_stale && (
                <p className="critic">
                  Le contexte a changé. Préparez une nouvelle proposition.
                </p>
              )}
              {p.status === "pending" && (
                <div className="decision-buttons">
                  <button
                    className="primary-button"
                    disabled={
                      disabled || group.proposal_stale || p.warnings.length > 0
                    }
                    onClick={() =>
                      run(() =>
                        api(
                          "/sessions/" + sid + "/decision",
                          post({ proposal_id: p.id, accept: true }),
                        ),
                      )
                    }
                  >
                    <Check size={14} /> Valider
                  </button>
                  <button
                    className="secondary-button"
                    disabled={disabled}
                    onClick={() =>
                      run(() =>
                        api(
                          "/sessions/" + sid + "/decision",
                          post({ proposal_id: p.id, accept: false }),
                        ),
                      )
                    }
                  >
                    <X size={14} /> Refuser
                  </button>
                </div>
              )}
              {["pending", "rejected", "completed"].includes(p.status) && (
                <button
                  className="alternative"
                  disabled={disabled}
                  onClick={() => prepare(true)}
                >
                  Chercher une autre solution <ArrowRight size={13} />
                </button>
              )}
            </div>
          )}
          {lastError && (
            <div className="error mission-error" role="alert">
              <b>Dernière erreur d'exécution</b>
              <p>{String(lastError.payload.message)}</p>
              <span>Corrigez le contexte ou relancez en mode démo.</span>
            </div>
          )}
          <div className="trace-heading">
            <button onClick={() => setTraceOpen(!traceOpen)}>
              <Activity size={14} /> TRACE DES OUTILS{" "}
              <span>
                {trace.filter((e) => e.kind === "tool.result").length}
              </span>
            </button>
          </div>
          {traceOpen && (
            <div className="trace-list">
              {trace.length === 0 ? (
                <p className="empty">
                  Les appels réels apparaîtront ici.
                  <br />
                  Chaque étape reste inspectable.
                </p>
              ) : (
                trace.slice(-40).map((e) => (
                  <details
                    key={e.id}
                    className={
                      "trace-item " +
                      (e.kind === "tool.started"
                        ? "started"
                        : e.kind === "mission.error"
                          ? "failed"
                          : "")
                    }
                  >
                    <summary>
                      <span className="trace-dot" />
                      <span>
                        {String(
                          e.payload.tool ??
                            e.kind
                              .replace("mission.", "")
                              .replace("decision.", "Validation · "),
                        )}
                        <small>
                          {e.kind === "tool.started"
                            ? "Appel MCP"
                            : e.kind === "tool.result"
                              ? "Résultat persisté"
                              : e.kind}
                        </small>
                      </span>
                      <time>
                        {new Date(e.time).toLocaleTimeString("fr-FR", {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </time>
                    </summary>
                    <pre>{JSON.stringify(e.payload, null, 2)}</pre>
                  </details>
                ))
              )}
            </div>
          )}
          <form
            className="physical-card"
            onSubmit={(e) => {
              e.preventDefault();
              action("card", { code });
            }}
          >
            <ScanLine size={18} />
            <div>
              <label htmlFor="card-code">Une carte, un nouveau contexte.</label>
              <div>
                <input
                  id="card-code"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Code papier · ACCES140"
                />
                <button aria-label="Ajouter la carte" disabled={disabled}>
                  <ArrowRight size={15} />
                </button>
              </div>
            </div>
          </form>
        </aside>
      </main>
      <footer className="app-footer">
        <span>
          <span className="live-dot" /> DONNÉES FICTIVES · STOCKAGE LOCAL
        </span>
        <span>AUCUNE CAPTURE D'ÉCRAN · AUCUN ENVOI EXTERNE</span>
        <a href={"/api/sessions/" + sid + "/export"}>
          <Download size={13} /> Exporter la trace
        </a>
      </footer>
      {doc && (
        <div className="modal-backdrop" onClick={() => setDoc(null)}>
          <section
            className="document-modal"
            role="dialog"
            aria-modal="true"
            aria-label={doc.title}
            onClick={(e) => e.stopPropagation()}
          >
            <header>
              <h2>{doc.title}</h2>
              <button
                className="icon-button"
                aria-label="Fermer le document"
                onClick={() => setDoc(null)}
              >
                <X size={20} />
              </button>
            </header>
            <pre>{doc.content}</pre>
            <button
              className="primary-button"
              onClick={() => {
                const url = URL.createObjectURL(
                  new Blob([doc.content], { type: "text/markdown" }),
                );
                const a = document.createElement("a");
                a.href = url;
                a.download = doc.title + ".md";
                a.click();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
              }}
            >
              <Download size={15} /> Télécharger
            </button>
          </section>
        </div>
      )}
    </div>
  );
}

function MiniPlan() {
  return (
    <svg
      className="mini-plan"
      viewBox="0 0 250 90"
      aria-label="Croquis fictif avec zone calme"
    >
      <rect
        x="4"
        y="4"
        width="242"
        height="82"
        rx="4"
        fill="#203328"
        stroke="#6c8565"
      />
      <rect x="12" y="12" width="138" height="36" fill="#476143" />
      <rect x="158" y="12" width="78" height="65" fill="#3b5035" />
      <rect x="12" y="55" width="104" height="24" fill="#849f6e" />
      <text x="23" y="34" fill="#e3eadb" fontSize="10">
        AGORA
      </text>
      <text x="171" y="42" fill="#e3eadb" fontSize="10">
        ATELIERS
      </text>
      <text x="22" y="71" fill="#132419" fontSize="10">
        ZONE CALME · 12
      </text>
      <path
        d="M132 72H150V50"
        stroke="#ccde9c"
        strokeDasharray="3 3"
        fill="none"
      />
    </svg>
  );
}

function Facilitator() {
  const [token, setToken] = useState(
    sessionStorage.getItem("work2030-admin") ?? "",
  );
  const [authed, setAuthed] = useState(false);
  const [groups, setGroups] = useState<Group[]>([]);
  const [error, setError] = useState("");
  const [confirmReset, setConfirmReset] = useState<string | null>(null);
  const [diagnostic, setDiagnostic] = useState<{
    id: string;
    events: Trace[];
  } | null>(null);
  const headers = { Authorization: "Bearer " + token };
  const refresh = useCallback(async () => {
    const g = await api<Group[]>("/admin/sessions", {
      headers: { Authorization: "Bearer " + token },
    });
    setGroups(g);
    setAuthed(true);
    sessionStorage.setItem("work2030-admin", token);
  }, [token]);
  useEffect(() => {
    if (!authed) return;
    const t = setInterval(
      () => refresh().catch((e) => setError(e.message)),
      2000,
    );
    return () => clearInterval(t);
  }, [authed, refresh]);
  const control = async (id: string, action: string, data: unknown = {}) => {
    try {
      setError("");
      await api("/admin/" + id + "/control", {
        ...post({ action, data }),
        headers,
      });
      await refresh();
      setConfirmReset(null);
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <div className="facilitator">
      <header className="app-header">
        <Brand />
        <span className="eyebrow">CONSOLE ANIMATEUR / CRTHON 10</span>
        <a className="text-link" href="/">
          Espaces participants <ArrowUpRight size={16} />
        </a>
      </header>
      <main>
        <div className="eyebrow">LE LABORATOIRE, EN UN REGARD</div>
        <h1>
          Cinq espaces.
          <br />
          <em>Une expérience partagée.</em>
        </h1>
        <p className="landing-copy">
          Pilotez les séquences, déclenchez un imprévu et préparez la prochaine
          session.
        </p>
        {!authed ? (
          <form
            className="admin-login"
            onSubmit={(e) => {
              e.preventDefault();
              refresh().catch((e) => setError(e.message));
            }}
          >
            <label htmlFor="admin-token">Code animateur (ANIMATOR_TOKEN)</label>
            <input
              id="admin-token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            <button className="primary-button">
              Ouvrir la console <ArrowRight size={16} />
            </button>
          </form>
        ) : (
          <>
            <div className="admin-toolbar">
              <span>
                <span className="live-dot" /> {groups.length}/5 ENVIRONNEMENTS
              </span>
              <button
                className="secondary-button"
                onClick={async () => {
                  try {
                    await api("/admin/seed", { ...post({}), headers });
                    await refresh();
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                Créer / vérifier les cinq sessions
              </button>
              <button
                className="secondary-button"
                onClick={() =>
                  control("all", "pause", {
                    paused: !groups.every((g) => g.state.paused),
                  })
                }
              >
                {groups.every((g) => g.state.paused) ? (
                  <Play size={14} />
                ) : (
                  <Pause size={14} />
                )}{" "}
                {groups.every((g) => g.state.paused)
                  ? "Reprendre tous"
                  : "Pause générale"}
              </button>
              <button
                className="danger-button"
                onClick={() => setConfirmReset("all")}
              >
                <RotateCcw size={14} /> Réinitialiser l'atelier
              </button>
            </div>
            <div className="admin-groups">
              {groups.map((g, i) => (
                <article className="admin-group" key={g.id}>
                  <div className="admin-group-top">
                    <span className="group-number">0{i + 1}</span>
                    <span
                      className={
                        "group-health " + (g.state.paused ? "paused" : "")
                      }
                    >
                      <span className="live-dot" />
                      {g.state.paused
                        ? "EN PAUSE"
                        : g.active
                          ? "OUTILS ACTIFS"
                          : "DISPONIBLE"}
                    </span>
                  </div>
                  <h2>{g.name}</h2>
                  <a
                    className="text-link"
                    href={"/g/" + g.id}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Ouvrir l'espace <ExternalLink size={14} />
                  </a>
                  <div className="admin-stats">
                    <span>
                      {g.state.context.length}
                      <small>sources actives</small>
                    </span>
                    <span>
                      {g.state.documents.length}
                      <small>documents</small>
                    </span>
                    <span>
                      {g.state.proposal?.status ?? "—"}
                      <small>décision</small>
                    </span>
                  </div>
                  <label>
                    Séquence
                    <select
                      aria-label={"Séquence " + g.name}
                      value={g.state.phase}
                      onChange={(e) =>
                        control(g.id, "phase", {
                          phase: Number(e.target.value),
                        })
                      }
                    >
                      {phases.map((p, i) => (
                        <option value={i} key={p}>
                          {i + 1}. {p} · {timings[i]}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="admin-group-actions">
                    <button
                      className="secondary-button"
                      onClick={() =>
                        control(g.id, "pause", { paused: !g.state.paused })
                      }
                    >
                      {g.state.paused ? (
                        <Play size={14} />
                      ) : (
                        <Pause size={14} />
                      )}{" "}
                      {g.state.paused ? "Reprendre" : "Pause"}
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => control(g.id, "perturb")}
                    >
                      <Radio size={14} /> Imprévu LED
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => setConfirmReset(g.id)}
                    >
                      <RotateCcw size={14} /> Reset
                    </button>
                    <button
                      className="secondary-button"
                      onClick={async () => {
                        try {
                          const events = await api<Trace[]>(
                            "/sessions/" + g.id + "/events",
                          );
                          setDiagnostic({ id: g.id, events });
                        } catch (e) {
                          setError((e as Error).message);
                        }
                      }}
                    >
                      <Activity size={14} /> Diagnostic
                    </button>
                  </div>
                  <p className="admin-cost">
                    Réservation API : {g.api_reserved_usd.toFixed(2)} $ · rév.{" "}
                    {g.revision}
                  </p>
                </article>
              ))}
            </div>
            <div className="facilitator-guide">
              <div>
                <h3>90 minutes, cinq moments.</h3>
                <p>
                  Introduction 8 min · Mémoire 20 min · Démonstration 20 min ·
                  Outils 30 min · Débrief 12 min. Faites tourner les rôles à
                  chaque transition.
                </p>
              </div>
              <a
                className="text-link"
                href="/cartes"
                target="_blank"
                rel="noreferrer"
              >
                Cartes imprimables <ScanLine size={17} />
              </a>
            </div>
          </>
        )}
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </main>
      {confirmReset && (
        <div className="modal-backdrop">
          <section
            className="confirm-modal"
            role="dialog"
            aria-label="Confirmer la réinitialisation"
          >
            <RotateCcw size={25} />
            <h2>
              Restaurer{" "}
              {confirmReset === "all" ? "les cinq environnements" : "ce groupe"}{" "}
              ?
            </h2>
            <p>
              Les objets, recettes et décisions sont remis au jeu initial. Les
              traces et réservations API restent conservées.
            </p>
            <div>
              <button
                className="secondary-button"
                onClick={() => setConfirmReset(null)}
              >
                Conserver
              </button>
              <button
                className="danger-button"
                onClick={() => control(confirmReset, "reset")}
              >
                Réinitialiser
              </button>
            </div>
          </section>
        </div>
      )}
      {diagnostic && (
        <div className="modal-backdrop">
          <section
            className="document-modal"
            role="dialog"
            aria-label="Diagnostic"
          >
            <header>
              <h2>Trace technique du groupe</h2>
              <button
                aria-label="Fermer le diagnostic"
                className="icon-button"
                onClick={() => setDiagnostic(null)}
              >
                <X />
              </button>
            </header>
            {diagnostic.events
              .filter(
                (e) =>
                  e.kind === "mission.error" ||
                  e.kind === "tool.started" ||
                  e.kind === "mission.completed",
              )
              .slice(-30)
              .map((e) => (
                <div key={e.id}>
                  <b>
                    {e.kind} · {e.time}
                  </b>
                  <pre>{JSON.stringify(e.payload, null, 2)}</pre>
                </div>
              ))}
            {diagnostic.events.filter((e) => e.kind === "mission.error")
              .length === 0 && <p>Aucune erreur de mission enregistrée.</p>}
          </section>
        </div>
      )}
    </div>
  );
}
