import { useState, useEffect, useCallback, useRef } from "react";
import { BookOpen, ChevronLeft, RefreshCw, Wifi, WifiOff } from "lucide-react";
import Agenda from "./components/Agenda.jsx";
import StoryPage from "./components/StoryPage.jsx";
import ProjectSwitcher from "./components/ProjectSwitcher.jsx";
import KnowledgePanel from "./components/KnowledgePanel.jsx";
import * as api from "./api.js";

const EMPTY = { projects: [], epics: [], stories: [], tasks: [], agents: [], knowledge: [] };
const POLL_MS = 4000;
const PROJECT_KEY = "tabula-project-id";

export default function App() {
  const [page, setPage] = useState("agenda"); // 'agenda' | 'story' | 'knowledge'
  const [state, setState] = useState(EMPTY);
  const [selectedProject, setSelectedProject] = useState(() => {
    try {
      return localStorage.getItem(PROJECT_KEY) || null;
    } catch {
      return null;
    }
  });
  const [selectedEpic, setSelectedEpic] = useState(null);
  const [selectedStory, setSelectedStory] = useState(null);
  const [drag, setDrag] = useState(null);
  const [online, setOnline] = useState(null); // null=sconosciuto, true/false
  const [apiUrl, setApiUrl] = useState(api.getBaseUrl());
  const dragging = useRef(false);

  // Carica lo snapshot completo
  const reload = useCallback(async () => {
    try {
      const s = await api.getState();
      setState(s);
      setOnline(true);
      const projects = s.projects || [];
      // assicura un progetto selezionato valido (default: il primo)
      setSelectedProject((cur) =>
        cur && projects.some((p) => p.id === cur)
          ? cur
          : projects[0]?.id || null
      );
    } catch (err) {
      console.error("reload failed:", err);
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload, apiUrl]);

  // Persiste il progetto selezionato
  useEffect(() => {
    try {
      if (selectedProject) localStorage.setItem(PROJECT_KEY, selectedProject);
    } catch {}
  }, [selectedProject]);

  // Mantiene valida l'epica selezionata rispetto al progetto attivo
  useEffect(() => {
    const epics = state.epics.filter((e) => e.project_id === selectedProject);
    setSelectedEpic((cur) =>
      cur && epics.some((e) => e.id === cur) ? cur : epics[0]?.id || null
    );
  }, [selectedProject, state.epics]);

  // Polling: aggiorna in automatico (sospeso durante un drag per non disturbare)
  useEffect(() => {
    const id = setInterval(() => {
      if (!dragging.current) reload();
    }, POLL_MS);
    return () => clearInterval(id);
  }, [reload]);

  // tiene traccia del drag per sospendere il polling
  useEffect(() => {
    dragging.current = drag !== null;
  }, [drag]);

  const openStory = (sid) => {
    setSelectedStory(sid);
    setPage("story");
  };

  const applyApiUrl = () => {
    api.setBaseUrl(apiUrl);
    setApiUrl(api.getBaseUrl());
    reload();
  };

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="logo">T</div>
          <div>
            <div className="title">Tabula</div>
            <div className="sub">Cruscotto agenti &amp; lavori</div>
          </div>
          <ProjectSwitcher
            projects={state.projects || []}
            selectedProject={selectedProject}
            onSelect={setSelectedProject}
            reload={reload}
          />
        </div>

        <div className="header-right">
          <div className="api-field" title="URL del backend">
            {online === false ? (
              <WifiOff size={14} color="var(--c-todo)" />
            ) : (
              <Wifi size={14} color="var(--c-done)" />
            )}
            <input
              className="api-input"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && applyApiUrl()}
              onBlur={applyApiUrl}
              spellCheck={false}
            />
          </div>

          {page !== "agenda" && (
            <button className="back-btn" onClick={() => setPage("agenda")}>
              <ChevronLeft size={16} /> Agenda
            </button>
          )}
          {page !== "knowledge" && (
            <button
              className="back-btn"
              onClick={() => setPage("knowledge")}
              title="Profilo progetto & knowledge card"
            >
              <BookOpen size={15} /> Knowledge
            </button>
          )}
          <button className="reset-btn" onClick={reload} title="Aggiorna ora">
            <RefreshCw size={15} />
          </button>
        </div>
      </header>

      <main className="main">
        {online === false && (
          <div className="offline-banner">
            Backend non raggiungibile su <code>{apiUrl}</code>. Verifica che il
            server sia avviato e l'URL corretto.
          </div>
        )}

        {page === "agenda" && (
          <Agenda
            state={state}
            reload={reload}
            selectedProject={selectedProject}
            selectedEpic={selectedEpic}
            setSelectedEpic={setSelectedEpic}
            openStory={openStory}
            drag={drag}
            setDrag={setDrag}
          />
        )}
        {page === "story" && (
          <StoryPage
            state={state}
            reload={reload}
            storyId={selectedStory}
            drag={drag}
            setDrag={setDrag}
          />
        )}
        {page === "knowledge" && (
          <KnowledgePanel state={state} selectedProject={selectedProject} />
        )}
      </main>
    </div>
  );
}
