import { useState } from "react";
import { Layers, Plus, Pencil, Trash2, ChevronRight } from "lucide-react";
import { COLS, colAccent, ColHeader, EditBox, PhaseBadge } from "./shared.jsx";
import * as api from "../api.js";
import { READONLY } from "../config.js";

// Home: epiche a sinistra (sezioni verticali), storie dell'epica selezionata a destra.
export default function Agenda({
  state,
  reload,
  selectedProject,
  selectedEpic,
  setSelectedEpic,
  openStory,
  drag,
  setDrag,
}) {
  return (
    <div className="agenda-layout">
      <EpicPanel
        state={state}
        reload={reload}
        selectedProject={selectedProject}
        selectedEpic={selectedEpic}
        setSelectedEpic={setSelectedEpic}
        drag={drag}
        setDrag={setDrag}
      />
      <StoryPanel
        state={state}
        reload={reload}
        selectedEpic={selectedEpic}
        openStory={openStory}
        drag={drag}
        setDrag={setDrag}
      />
    </div>
  );
}

// ---- Sinistra: epiche in tre sezioni verticali ----
function EpicPanel({ state, reload, selectedProject, selectedEpic, setSelectedEpic, drag, setDrag }) {
  const [adding, setAdding] = useState(null);
  const [form, setForm] = useState({ title: "", desc: "" });
  const [editing, setEditing] = useState(null);

  const add = async (status) => {
    if (!form.title.trim() || !selectedProject) return;
    await api.epics.create({
      title: form.title,
      desc: form.desc,
      status,
      project_id: selectedProject,
    });
    setForm({ title: "", desc: "" });
    setAdding(null);
    reload();
  };
  const save = async (id, patch) => {
    await api.epics.update(id, patch);
    setEditing(null);
    reload();
  };
  const del = async (id) => {
    await api.epics.remove(id);
    reload();
  };
  const onDrop = async (status) => {
    if (!drag || drag.kind !== "epic") return;
    await api.epics.update(drag.id, { status });
    setDrag(null);
    reload();
  };

  if (!selectedProject)
    return (
      <div className="epic-panel">
        <div className="panel-title">
          <Layers size={15} /> Epiche
        </div>
        <div className="empty">
          Nessun progetto selezionato. Creane uno dall'header.
        </div>
      </div>
    );

  return (
    <div className="epic-panel">
      <div className="panel-title">
        <Layers size={15} /> Epiche
      </div>
      <div className="epic-sections">
        {COLS.map((col) => {
          const items = state.epics.filter(
            (e) => e.status === col.key && e.project_id === selectedProject
          );
          return (
            <div
              key={col.key}
              className="epic-section"
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => onDrop(col.key)}
            >
              <div className="section-header">
                <span className="col-dot" style={{ background: colAccent[col.key] }} />
                <span className="section-title">{col.label}</span>
                <span className="col-count">{items.length}</span>
              </div>
              <div className="epic-list">
                {items.map((e) => (
                  <div
                    key={e.id}
                    draggable={!READONLY}
                    onDragStart={() => !READONLY && setDrag({ kind: "epic", id: e.id })}
                    onDragEnd={() => setDrag(null)}
                    onClick={() => setSelectedEpic(e.id)}
                    className={`epic-card${selectedEpic === e.id ? " selected" : ""}`}
                    style={{ borderLeft: `3px solid ${colAccent[col.key]}` }}
                  >
                    {editing === e.id ? (
                      <EditBox
                        item={e}
                        onSave={(p) => save(e.id, p)}
                        onCancel={() => setEditing(null)}
                      />
                    ) : (
                      <>
                        <div className="card-top">
                          <div className="epic-title">{e.title}</div>
                          {!READONLY && (
                            <div className="card-actions">
                              <button
                                className="icon-btn"
                                onClick={(ev) => {
                                  ev.stopPropagation();
                                  setEditing(e.id);
                                }}
                              >
                                <Pencil size={12} />
                              </button>
                              <button
                                className="icon-btn"
                                onClick={(ev) => {
                                  ev.stopPropagation();
                                  del(e.id);
                                }}
                              >
                                <Trash2 size={12} />
                              </button>
                            </div>
                          )}
                        </div>
                        {e.desc && <div className="card-desc">{e.desc}</div>}
                        <div className="epic-meta">
                          {state.stories.filter((s) => s.epic_id === e.id).length} storie
                        </div>
                      </>
                    )}
                  </div>
                ))}
                {!READONLY &&
                  (adding === col.key ? (
                    <div className="add-form">
                      <input
                        autoFocus
                        placeholder="Titolo epica"
                        value={form.title}
                        onChange={(ev) => setForm((f) => ({ ...f, title: ev.target.value }))}
                        onKeyDown={(ev) => ev.key === "Enter" && add(col.key)}
                        className="input"
                      />
                      <input
                        placeholder="Descrizione"
                        value={form.desc}
                        onChange={(ev) => setForm((f) => ({ ...f, desc: ev.target.value }))}
                        className="input"
                      />
                      <div className="form-row">
                        <button className="btn-primary" onClick={() => add(col.key)}>
                          Aggiungi
                        </button>
                        <button
                          className="btn-ghost"
                          onClick={() => {
                            setAdding(null);
                            setForm({ title: "", desc: "" });
                          }}
                        >
                          Annulla
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button className="add-btn-sm" onClick={() => setAdding(col.key)}>
                      <Plus size={13} /> Epica
                    </button>
                  ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---- Destra: storie dell'epica selezionata (Kanban) ----
function StoryPanel({ state, reload, selectedEpic, openStory, drag, setDrag }) {
  const [adding, setAdding] = useState(null);
  const [form, setForm] = useState({ title: "", desc: "" });
  const [editing, setEditing] = useState(null);
  const epic = state.epics.find((e) => e.id === selectedEpic);

  const add = async (status) => {
    if (!form.title.trim() || !epic) return;
    await api.stories.create({
      title: form.title,
      desc: form.desc,
      status,
      epic_id: epic.id,
    });
    setForm({ title: "", desc: "" });
    setAdding(null);
    reload();
  };
  const save = async (id, patch) => {
    await api.stories.update(id, patch);
    setEditing(null);
    reload();
  };
  const del = async (id) => {
    await api.stories.remove(id);
    reload();
  };
  const onDrop = async (status) => {
    if (!drag || drag.kind !== "story") return;
    await api.stories.update(drag.id, { status });
    setDrag(null);
    reload();
  };

  if (!epic)
    return (
      <div className="story-panel">
        <div className="empty">Seleziona un'epica a sinistra.</div>
      </div>
    );

  return (
    <div className="story-panel">
      <div className="panel-title">
        <span className="badge" style={{ background: "var(--epic)" }}>
          EPICA
        </span>
        <span className="panel-epic-name">{epic.title}</span>
      </div>
      <div className="board">
        {COLS.map((col) => {
          const items = state.stories.filter(
            (s) => s.epic_id === epic.id && s.status === col.key
          );
          return (
            <div
              key={col.key}
              className="col"
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => onDrop(col.key)}
            >
              <ColHeader col={col} count={items.length} />
              <div className="col-body">
                {items.map((it) => (
                  <div
                    key={it.id}
                    draggable={!READONLY}
                    onDragStart={() => !READONLY && setDrag({ kind: "story", id: it.id })}
                    onDragEnd={() => setDrag(null)}
                    className="card"
                    style={{ borderLeft: `3px solid ${colAccent[col.key]}` }}
                  >
                    {editing === it.id ? (
                      <EditBox
                        item={it}
                        onSave={(p) => save(it.id, p)}
                        onCancel={() => setEditing(null)}
                      />
                    ) : (
                      <>
                        <div className="card-top">
                          <span style={{ display: "flex", gap: 6, alignItems: "center" }}>
                            <span className="badge" style={{ background: "var(--story)" }}>
                              STORIA
                            </span>
                            <PhaseBadge phase={it.phase} />
                          </span>
                          {!READONLY && (
                            <div className="card-actions">
                              <button className="icon-btn" onClick={() => setEditing(it.id)}>
                                <Pencil size={13} />
                              </button>
                              <button className="icon-btn" onClick={() => del(it.id)}>
                                <Trash2 size={13} />
                              </button>
                            </div>
                          )}
                        </div>
                        <div className="card-title">{it.title}</div>
                        {it.desc && <div className="card-desc">{it.desc}</div>}
                        <button className="open-btn" onClick={() => openStory(it.id)}>
                          Apri <ChevronRight size={13} />
                        </button>
                      </>
                    )}
                  </div>
                ))}
                {!READONLY &&
                  (adding === col.key ? (
                    <div className="add-form">
                      <input
                        autoFocus
                        placeholder="Titolo storia"
                        value={form.title}
                        onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                        onKeyDown={(e) => e.key === "Enter" && add(col.key)}
                        className="input"
                      />
                      <input
                        placeholder="Descrizione"
                        value={form.desc}
                        onChange={(e) => setForm((f) => ({ ...f, desc: e.target.value }))}
                        className="input"
                      />
                      <div className="form-row">
                        <button className="btn-primary" onClick={() => add(col.key)}>
                          Aggiungi
                        </button>
                        <button
                          className="btn-ghost"
                          onClick={() => {
                            setAdding(null);
                            setForm({ title: "", desc: "" });
                          }}
                        >
                          Annulla
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button className="add-btn" onClick={() => setAdding(col.key)}>
                      <Plus size={15} /> Aggiungi
                    </button>
                  ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
