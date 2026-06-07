import { useState } from "react";

export const COLS = [
  { key: "todo", label: "To Do" },
  { key: "progress", label: "In Progress" },
  { key: "done", label: "Done" },
];

export const colAccent = {
  todo: "var(--c-todo)",
  progress: "var(--c-prog)",
  done: "var(--c-done)",
};

export function ColHeader({ col, count }) {
  return (
    <div className="col-header">
      <span className="col-dot" style={{ background: colAccent[col.key] }} />
      <span className="col-title">{col.label}</span>
      <span className="col-count">{count}</span>
    </div>
  );
}

// Form inline per modificare titolo + descrizione (epiche e storie)
export function EditBox({ item, onSave, onCancel }) {
  const [title, setTitle] = useState(item.title);
  const [desc, setDesc] = useState(item.desc || "");
  return (
    <div className="add-form" onClick={(e) => e.stopPropagation()}>
      <input
        autoFocus
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="input"
        placeholder="Titolo"
      />
      <input
        value={desc}
        onChange={(e) => setDesc(e.target.value)}
        className="input"
        placeholder="Descrizione"
      />
      <div className="form-row">
        <button className="btn-primary" onClick={() => onSave({ title, desc })}>
          Salva
        </button>
        <button className="btn-ghost" onClick={onCancel}>
          Annulla
        </button>
      </div>
    </div>
  );
}

// ---- Fasi della storia (phase) ----
export const PHASE_LABELS = {
  analysis: "Analisi",
  ux: "UX",
  design: "Design",
  dev: "Dev",
  done: "Done",
};
const PHASE_COLORS = {
  analysis: "#8b6fd6",
  ux: "#d67fb0",
  design: "#4a90d9",
  dev: "#e0a020",
  done: "#3fae5a",
};

export function PhaseBadge({ phase }) {
  if (!phase) return null;
  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: 0.4,
        padding: "2px 7px",
        borderRadius: 6,
        color: "#fff",
        background: PHASE_COLORS[phase] || "var(--muted)",
      }}
    >
      {PHASE_LABELS[phase] || phase}
    </span>
  );
}

// ---- Mini-renderer Markdown (dependency-free) ----
// Input escaped -> output HTML sicuro (solo tag generati qui). I mockup HTML
// NON passano da qui: vengono isolati in un iframe sandbox (vedi MdView).
function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function inlineMd(s) {
  // s è già escaped
  return s
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
}
function renderMarkdown(md) {
  const lines = esc(md).split(/\r?\n/);
  let html = "";
  let inList = false;
  let inCode = false;
  let code = "";
  const closeList = () => {
    if (inList) {
      html += "</ul>";
      inList = false;
    }
  };
  for (const line of lines) {
    if (/^```/.test(line)) {
      if (inCode) {
        html += "<pre><code>" + code + "</code></pre>";
        code = "";
        inCode = false;
      } else {
        closeList();
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      code += line + "\n";
      continue;
    }
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      closeList();
      const lvl = h[1].length;
      html += `<h${lvl}>` + inlineMd(h[2]) + `</h${lvl}>`;
      continue;
    }
    const li = line.match(/^\s*[-*]\s+(.*)$/);
    if (li) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += "<li>" + inlineMd(li[1]) + "</li>";
      continue;
    }
    if (line.trim() === "") {
      closeList();
      continue;
    }
    closeList();
    html += "<p>" + inlineMd(line) + "</p>";
  }
  if (inCode) html += "<pre><code>" + code + "</code></pre>";
  closeList();
  return html;
}

// ---- Render del documento MD (markdown + mockup HTML in iframe sandbox) ----
function splitMockups(md) {
  const re = /```mockup\s*([\s\S]*?)```/g;
  const parts = [];
  let last = 0;
  let m;
  while ((m = re.exec(md))) {
    if (m.index > last) parts.push({ type: "md", content: md.slice(last, m.index) });
    parts.push({ type: "mockup", content: m[1] });
    last = re.lastIndex;
  }
  if (last < md.length) parts.push({ type: "md", content: md.slice(last) });
  return parts;
}

export function MdView({ md }) {
  if (!md || !md.trim())
    return <div className="empty">Nessun documento associato.</div>;
  const parts = splitMockups(md);
  return (
    <div className="md-view" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {parts.map((p, i) =>
        p.type === "mockup" ? (
          <iframe
            key={i}
            title={`mockup-${i}`}
            sandbox=""
            srcDoc={p.content}
            style={{
              width: "100%",
              minHeight: 360,
              border: "1px solid var(--border, #2a2a3a)",
              borderRadius: 8,
              background: "#fff",
            }}
          />
        ) : (
          <div
            key={i}
            className="md-prose"
            style={{ lineHeight: 1.5, fontSize: 14 }}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(p.content || "") }}
          />
        )
      )}
    </div>
  );
}

// Editor MD: textarea + salva
export function MdEditor({ value, onSave }) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(value || "");
  if (!editing) {
    return (
      <div>
        <button className="btn-ghost" onClick={() => { setText(value || ""); setEditing(true); }}>
          ✎ Modifica documento
        </button>
        <MdView md={value} />
      </div>
    );
  }
  return (
    <div className="add-form">
      <textarea
        autoFocus
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="input"
        style={{ minHeight: 220, fontFamily: "monospace", fontSize: 13 }}
        placeholder="Documento Markdown (supporta blocchi ```mockup``` HTML)…"
      />
      <div className="form-row">
        <button className="btn-primary" onClick={() => { onSave(text); setEditing(false); }}>
          Salva
        </button>
        <button className="btn-ghost" onClick={() => setEditing(false)}>
          Annulla
        </button>
      </div>
    </div>
  );
}
