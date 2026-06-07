import { useState } from "react";
import { Trello, Cpu, FileText, ChevronRight } from "lucide-react";
import Munera from "./Munera.jsx";
import Periti from "./Periti.jsx";
import { PhaseBadge, MdEditor } from "./shared.jsx";
import * as api from "../api.js";

// Pagina di dettaglio di una storia: tab Munera (task) + Periti (agenti) + Documento (MD).
export default function StoryPage({ state, reload, storyId, drag, setDrag }) {
  const [tab, setTab] = useState("munera");
  const story = state.stories.find((s) => s.id === storyId);
  const epic = story ? state.epics.find((e) => e.id === story.epic_id) : null;

  if (!story) return <div className="empty">Storia non trovata.</div>;

  const saveMd = async (md) => {
    await api.stories.update(storyId, { md });
    reload();
  };

  const tabs = [
    { k: "munera", label: "Munera", icon: Trello },
    { k: "periti", label: "Periti", icon: Cpu },
    { k: "doc", label: "Documento", icon: FileText },
  ];

  return (
    <div className="story-page">
      <div className="breadcrumb">
        {epic && <span className="crumb-epic">{epic.title}</span>}
        {epic && <ChevronRight size={13} style={{ color: "var(--muted)" }} />}
        <span className="crumb-story">{story.title}</span>
        <PhaseBadge phase={story.phase} />
      </div>
      <div className="sub-tabs">
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              className={`sub-tab${tab === t.k ? " active" : ""}`}
            >
              <Icon size={15} /> {t.label}
            </button>
          );
        })}
      </div>
      {tab === "munera" && (
        <Munera
          state={state}
          reload={reload}
          storyId={storyId}
          drag={drag}
          setDrag={setDrag}
        />
      )}
      {tab === "periti" && <Periti state={state} reload={reload} />}
      {tab === "doc" && (
        <div style={{ padding: "4px 2px" }}>
          <MdEditor value={story.md} onSave={saveMd} />
        </div>
      )}
    </div>
  );
}
