import { useState } from "react";
import { Plus, Pencil, Trash2, Activity, Zap } from "lucide-react";
import * as api from "../api.js";
import { READONLY } from "../config.js";

// Griglia degli agenti: stato, task corrente, token consumati.
export default function Periti({ state, reload }) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(null);

  const agents = state.agents;
  const total = agents.reduce((s, a) => s + a.tokens, 0);
  const maxT = Math.max(...agents.map((a) => a.tokens), 1);
  const activeCount = agents.filter((a) => a.status === "active").length;
  const fmt = (n) => n.toLocaleString("it-IT");

  const add = async () => {
    if (!name.trim()) return;
    await api.agents.create({
      name,
      current_task: "Inattivo",
      status: "idle",
      tokens: 0,
    });
    setName("");
    setAdding(false);
    reload();
  };
  const save = async (id, patch) => {
    await api.agents.update(id, patch);
    reload();
  };
  const del = async (id) => {
    await api.agents.remove(id);
    reload();
  };

  return (
    <div className="periti">
      <div className="stats">
        <Stat
          icon={Activity}
          label="Agenti attivi"
          value={`${activeCount} / ${agents.length}`}
          accent="var(--c-prog)"
        />
        <Stat icon={Zap} label="Token totali" value={fmt(total)} accent="var(--epic)" />
      </div>
      <div className="agent-grid">
        {agents.map((a) => (
          <div key={a.id} className="agent-card">
            {editing === a.id ? (
              <div className="add-form">
                <input
                  defaultValue={a.name}
                  onBlur={(e) => save(a.id, { name: e.target.value })}
                  className="input"
                  placeholder="Nome"
                />
                <input
                  defaultValue={a.current_task}
                  onBlur={(e) => save(a.id, { current_task: e.target.value })}
                  className="input"
                  placeholder="Task corrente"
                />
                <input
                  type="number"
                  defaultValue={a.tokens}
                  onBlur={(e) => save(a.id, { tokens: parseInt(e.target.value) || 0 })}
                  className="input"
                  placeholder="Token"
                />
                <select
                  value={a.status}
                  onChange={(e) => save(a.id, { status: e.target.value })}
                  className="input"
                >
                  <option value="active">Attivo</option>
                  <option value="idle">Inattivo</option>
                </select>
                <button className="btn-primary" onClick={() => setEditing(null)}>
                  Fatto
                </button>
              </div>
            ) : (
              <>
                <div className="agent-top">
                  <div className="agent-avatar">{a.name[0]}</div>
                  <div style={{ flex: 1 }}>
                    <div className="agent-name">{a.name}</div>
                    <div className="status-row">
                      <span
                        className="dot"
                        style={{
                          background:
                            a.status === "active" ? "var(--c-done)" : "var(--muted)",
                        }}
                      />
                      <span className="status-text">
                        {a.status === "active" ? "Attivo" : "Inattivo"}
                      </span>
                    </div>
                  </div>
                  {!READONLY && (
                    <div className="card-actions">
                      <button className="icon-btn" onClick={() => setEditing(a.id)}>
                        <Pencil size={13} />
                      </button>
                      <button className="icon-btn" onClick={() => del(a.id)}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  )}
                </div>
                <div className="task-box">
                  <span className="task-label">Sta facendo</span>
                  <span className="task-val">{a.current_task}</span>
                </div>
                <div className="token-box">
                  <div className="token-head">
                    <span className="task-label">Token consumati</span>
                    <span className="token-val">{fmt(a.tokens)}</span>
                  </div>
                  <div className="bar-bg">
                    <div
                      className="bar-fill"
                      style={{ width: `${(a.tokens / maxT) * 100}%` }}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        ))}
        {!READONLY &&
          (adding ? (
            <div className="agent-card" style={{ justifyContent: "center" }}>
              <div className="add-form">
                <input
                  autoFocus
                  placeholder="Nome agente"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && add()}
                  className="input"
                />
                <div className="form-row">
                  <button className="btn-primary" onClick={add}>
                    Aggiungi
                  </button>
                  <button
                    className="btn-ghost"
                    onClick={() => {
                      setAdding(false);
                      setName("");
                    }}
                  >
                    Annulla
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <button className="add-agent" onClick={() => setAdding(true)}>
              <Plus size={18} /> Nuovo agente
            </button>
          ))}
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, accent }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: accent }}>
        <Icon size={18} color="var(--ink)" />
      </div>
      <div>
        <div className="stat-val">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}
