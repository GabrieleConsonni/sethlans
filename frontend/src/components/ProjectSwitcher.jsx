import { useState, useEffect, useRef } from "react";
import { FolderKanban, Plus, ChevronDown, Check } from "lucide-react";
import * as api from "../api.js";

// Selettore di progetto nell'header: combo per scegliere il progetto attivo
// + form per crearne uno nuovo (Jira o interno).
export default function ProjectSwitcher({ projects, selectedProject, onSelect, reload }) {
  const [open, setOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", type: "jira", jira_key: "" });
  const ref = useRef(null);

  // chiude il pannello al click fuori
  useEffect(() => {
    if (!open) return;
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
        setAdding(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const current = projects.find((p) => p.id === selectedProject);

  const create = async () => {
    if (!form.name.trim()) return;
    const created = await api.projects.create({
      name: form.name.trim(),
      type: form.type,
      jira_key: form.type === "jira" ? form.jira_key.trim() : "",
    });
    setForm({ name: "", type: "jira", jira_key: "" });
    setAdding(false);
    setOpen(false);
    await reload();
    onSelect(created.id);
  };

  return (
    <div className="project-switcher" ref={ref}>
      <button className="project-trigger" onClick={() => setOpen((o) => !o)}>
        <FolderKanban size={15} />
        <span className="project-current">
          {current ? current.name : "Nessun progetto"}
        </span>
        {current?.jira_key && <span className="project-key">{current.jira_key}</span>}
        <ChevronDown size={14} style={{ color: "var(--muted)" }} />
      </button>

      {open && (
        <div className="project-menu">
          <div className="project-list">
            {projects.length === 0 && (
              <div className="project-empty">Nessun progetto. Creane uno.</div>
            )}
            {projects.map((p) => (
              <button
                key={p.id}
                className={`project-item${p.id === selectedProject ? " active" : ""}`}
                onClick={() => {
                  onSelect(p.id);
                  setOpen(false);
                }}
              >
                <span className="project-item-name">{p.name}</span>
                {p.jira_key && <span className="project-key">{p.jira_key}</span>}
                {p.id === selectedProject && (
                  <Check size={14} style={{ marginLeft: "auto", color: "var(--c-done)" }} />
                )}
              </button>
            ))}
          </div>

          {adding ? (
            <div className="add-form" style={{ margin: "8px" }}>
              <input
                autoFocus
                className="input"
                placeholder="Nome progetto"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                onKeyDown={(e) => e.key === "Enter" && create()}
              />
              <select
                className="input"
                value={form.type}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
              >
                <option value="jira">Progetto Jira</option>
                <option value="internal">Progetto interno</option>
              </select>
              {form.type === "jira" && (
                <input
                  className="input"
                  placeholder="Chiave Jira (es. ABC)"
                  value={form.jira_key}
                  onChange={(e) => setForm((f) => ({ ...f, jira_key: e.target.value }))}
                  onKeyDown={(e) => e.key === "Enter" && create()}
                />
              )}
              <div className="form-row">
                <button className="btn-primary" onClick={create}>
                  Crea
                </button>
                <button
                  className="btn-ghost"
                  onClick={() => {
                    setAdding(false);
                    setForm({ name: "", type: "jira", jira_key: "" });
                  }}
                >
                  Annulla
                </button>
              </div>
            </div>
          ) : (
            <button className="project-add" onClick={() => setAdding(true)}>
              <Plus size={14} /> Nuovo progetto
            </button>
          )}
        </div>
      )}
    </div>
  );
}
