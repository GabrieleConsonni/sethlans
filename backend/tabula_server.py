"""
Tabula — Backend API
=====================
Server CRUD per epiche, storie, task e agenti. Chiamabile dall'interfaccia
Tabula e dai subagenti di Claude.

Persistenza: Postgres (schema `tabula`) via SQLAlchemy. Le tabelle sono gestite
con Alembic — prima dell'avvio eseguire:
    pip install -r requirements.txt
    alembic upgrade head
    python tabula_server.py
Docs interattive: http://localhost:9955/docs

Connessione: env `TABULA_DB_URL` (vedi db.py). Porta: env `TABULA_PORT` (default 9955).

Estensioni rispetto alla versione SQLite:
- ogni entità (epic/story/task) ha un campo `md` (+ `md_updated_at`) per il
  documento Markdown associato;
- le storie hanno una `phase` (analysis|ux|design|dev|done) per il flusso PO→UX→architect→dev.
"""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import SessionLocal
from models import (
    KIND_KNOWLEDGE,
    PHASE_STORY,
    ROLE_KNOWLEDGE,
    SOURCE_KNOWLEDGE,
    STATUS_AGENT,
    STATUS_WORK,
    TYPE_PROJECT,
    Agent,
    Epic,
    Knowledge,
    Project,
    Story,
    Task,
    new_id,
)

# ----------------------------- Schemi (API contract) -----------------------------


class ProjectIn(BaseModel):
    name: str
    type: str = "internal"
    jira_key: str = ""
    md: str = ""
    config: dict = {}

class ProjectPatch(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    jira_key: Optional[str] = None
    md: Optional[str] = None
    config: Optional[dict] = None


class KnowledgeIn(BaseModel):
    project_id: str
    title: str
    role: str = "general"
    kind: str = "kb"
    source: str = "manual"
    md: str = ""

class KnowledgePatch(BaseModel):
    title: Optional[str] = None
    role: Optional[str] = None
    kind: Optional[str] = None
    source: Optional[str] = None
    md: Optional[str] = None


class EpicIn(BaseModel):
    title: str
    desc: str = ""
    status: str = "todo"
    project_id: str
    md: str = ""

class EpicPatch(BaseModel):
    title: Optional[str] = None
    desc: Optional[str] = None
    status: Optional[str] = None
    project_id: Optional[str] = None
    md: Optional[str] = None


class StoryIn(BaseModel):
    title: str
    desc: str = ""
    status: str = "todo"
    phase: str = "analysis"
    epic_id: str
    md: str = ""

class StoryPatch(BaseModel):
    title: Optional[str] = None
    desc: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    epic_id: Optional[str] = None
    md: Optional[str] = None


class TaskIn(BaseModel):
    title: str
    status: str = "todo"
    story_id: str
    agent_id: Optional[str] = None
    md: str = ""

class TaskPatch(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    story_id: Optional[str] = None
    agent_id: Optional[str] = None
    md: Optional[str] = None


class AgentIn(BaseModel):
    name: str
    current_task: str = "Inattivo"
    status: str = "idle"
    tokens: int = 0

class AgentPatch(BaseModel):
    name: Optional[str] = None
    current_task: Optional[str] = None
    status: Optional[str] = None
    tokens: Optional[int] = None


# ----------------------------- App -----------------------------

app = FastAPI(title="Tabula API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # in produzione: restringere
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


# ----------------------------- Helpers -----------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def validate_status(value, allowed, field="status"):
    if value is not None and value not in allowed:
        raise HTTPException(422, f"{field} non valido: deve essere uno tra {sorted(allowed)}")


def fetch_or_404(db: Session, model, _id: str):
    obj = db.get(model, _id)
    if not obj:
        raise HTTPException(404, f"{model.__tablename__[:-1]} '{_id}' non trovato")
    return obj


def apply_md_timestamp(obj, patch_dict):
    """Se l'MD viene modificato, aggiorna md_updated_at."""
    if patch_dict.get("md") is not None and hasattr(obj, "md_updated_at"):
        obj.md_updated_at = _now()


# ---------- PROJECTS ----------

@app.get("/projects")
def list_projects(type: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Project)
    if type:
        q = q.filter(Project.type == type)
    return [p.to_dict() for p in q.all()]

@app.post("/projects", status_code=201)
def create_project(body: ProjectIn, db: Session = Depends(get_db)):
    validate_status(body.type, TYPE_PROJECT, field="type")
    project = Project(
        id=new_id("p"), name=body.name, type=body.type, jira_key=body.jira_key,
        md=body.md, config=body.config or {},
        md_updated_at=_now() if body.md else None,
    )
    db.add(project); db.commit()
    return project.to_dict()

@app.get("/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    return fetch_or_404(db, Project, project_id).to_dict()

@app.patch("/projects/{project_id}")
def update_project(project_id: str, body: ProjectPatch, db: Session = Depends(get_db)):
    validate_status(body.type, TYPE_PROJECT, field="type")
    project = fetch_or_404(db, Project, project_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    apply_md_timestamp(project, data)
    for k, v in data.items():
        setattr(project, k, v)
    db.commit()
    return project.to_dict()

@app.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    db.delete(fetch_or_404(db, Project, project_id)); db.commit()
    return {"deleted": project_id}


# ---------- EPICS ----------

@app.get("/epics")
def list_epics(status: Optional[str] = None, project_id: Optional[str] = None,
               db: Session = Depends(get_db)):
    q = db.query(Epic)
    if status:
        q = q.filter(Epic.status == status)
    if project_id:
        q = q.filter(Epic.project_id == project_id)
    return [e.to_dict() for e in q.all()]

@app.post("/epics", status_code=201)
def create_epic(body: EpicIn, db: Session = Depends(get_db)):
    validate_status(body.status, STATUS_WORK)
    fetch_or_404(db, Project, body.project_id)
    epic = Epic(
        id=new_id("e"), title=body.title, desc=body.desc, status=body.status,
        project_id=body.project_id, md=body.md,
        md_updated_at=_now() if body.md else None,
    )
    db.add(epic); db.commit()
    return epic.to_dict()

@app.get("/epics/{epic_id}")
def get_epic(epic_id: str, db: Session = Depends(get_db)):
    return fetch_or_404(db, Epic, epic_id).to_dict()

@app.patch("/epics/{epic_id}")
def update_epic(epic_id: str, body: EpicPatch, db: Session = Depends(get_db)):
    validate_status(body.status, STATUS_WORK)
    epic = fetch_or_404(db, Epic, epic_id)
    if body.project_id is not None:
        fetch_or_404(db, Project, body.project_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    apply_md_timestamp(epic, data)
    for k, v in data.items():
        setattr(epic, k, v)
    db.commit()
    return epic.to_dict()

@app.delete("/epics/{epic_id}")
def delete_epic(epic_id: str, db: Session = Depends(get_db)):
    db.delete(fetch_or_404(db, Epic, epic_id)); db.commit()
    return {"deleted": epic_id}


# ---------- STORIES ----------

@app.get("/stories")
def list_stories(epic_id: Optional[str] = None, status: Optional[str] = None,
                 phase: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Story)
    if epic_id:
        q = q.filter(Story.epic_id == epic_id)
    if status:
        q = q.filter(Story.status == status)
    if phase:
        q = q.filter(Story.phase == phase)
    return [s.to_dict() for s in q.all()]

@app.post("/stories", status_code=201)
def create_story(body: StoryIn, db: Session = Depends(get_db)):
    validate_status(body.status, STATUS_WORK)
    validate_status(body.phase, PHASE_STORY, field="phase")
    fetch_or_404(db, Epic, body.epic_id)
    story = Story(
        id=new_id("s"), title=body.title, desc=body.desc, status=body.status,
        phase=body.phase, epic_id=body.epic_id, md=body.md,
        md_updated_at=_now() if body.md else None,
    )
    db.add(story); db.commit()
    return story.to_dict()

@app.get("/stories/{story_id}")
def get_story(story_id: str, db: Session = Depends(get_db)):
    return fetch_or_404(db, Story, story_id).to_dict()

@app.patch("/stories/{story_id}")
def update_story(story_id: str, body: StoryPatch, db: Session = Depends(get_db)):
    validate_status(body.status, STATUS_WORK)
    validate_status(body.phase, PHASE_STORY, field="phase")
    story = fetch_or_404(db, Story, story_id)
    if body.epic_id is not None:
        fetch_or_404(db, Epic, body.epic_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    apply_md_timestamp(story, data)
    for k, v in data.items():
        setattr(story, k, v)
    db.commit()
    return story.to_dict()

@app.delete("/stories/{story_id}")
def delete_story(story_id: str, db: Session = Depends(get_db)):
    db.delete(fetch_or_404(db, Story, story_id)); db.commit()
    return {"deleted": story_id}


# ---------- TASKS ----------

@app.get("/tasks")
def list_tasks(story_id: Optional[str] = None, status: Optional[str] = None,
               agent_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Task)
    if story_id:
        q = q.filter(Task.story_id == story_id)
    if status:
        q = q.filter(Task.status == status)
    if agent_id:
        q = q.filter(Task.agent_id == agent_id)
    return [t.to_dict() for t in q.all()]

@app.post("/tasks", status_code=201)
def create_task(body: TaskIn, db: Session = Depends(get_db)):
    validate_status(body.status, STATUS_WORK)
    fetch_or_404(db, Story, body.story_id)
    if body.agent_id:
        fetch_or_404(db, Agent, body.agent_id)
    task = Task(
        id=new_id("t"), title=body.title, status=body.status, story_id=body.story_id,
        agent_id=body.agent_id, md=body.md, md_updated_at=_now() if body.md else None,
    )
    db.add(task); db.commit()
    return task.to_dict()

@app.get("/tasks/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    return fetch_or_404(db, Task, task_id).to_dict()

@app.patch("/tasks/{task_id}")
def update_task(task_id: str, body: TaskPatch, db: Session = Depends(get_db)):
    validate_status(body.status, STATUS_WORK)
    task = fetch_or_404(db, Task, task_id)
    if body.story_id is not None:
        fetch_or_404(db, Story, body.story_id)
    if body.agent_id is not None and body.agent_id != "":
        fetch_or_404(db, Agent, body.agent_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    apply_md_timestamp(task, data)
    for k, v in data.items():
        setattr(task, k, v)
    db.commit()
    return task.to_dict()

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    db.delete(fetch_or_404(db, Task, task_id)); db.commit()
    return {"deleted": task_id}


# ---------- AGENTS ----------

@app.get("/agents")
def list_agents(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Agent)
    if status:
        q = q.filter(Agent.status == status)
    return [a.to_dict() for a in q.all()]

@app.post("/agents", status_code=201)
def create_agent(body: AgentIn, db: Session = Depends(get_db)):
    validate_status(body.status, STATUS_AGENT)
    agent = Agent(id=new_id("a"), name=body.name, current_task=body.current_task,
                  status=body.status, tokens=body.tokens)
    db.add(agent); db.commit()
    return agent.to_dict()

@app.get("/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    return fetch_or_404(db, Agent, agent_id).to_dict()

@app.patch("/agents/{agent_id}")
def update_agent(agent_id: str, body: AgentPatch, db: Session = Depends(get_db)):
    validate_status(body.status, STATUS_AGENT)
    agent = fetch_or_404(db, Agent, agent_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    for k, v in data.items():
        setattr(agent, k, v)
    db.commit()
    return agent.to_dict()

@app.delete("/agents/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    db.delete(fetch_or_404(db, Agent, agent_id)); db.commit()
    return {"deleted": agent_id}


# ---------- KNOWLEDGE ----------

@app.get("/knowledge")
def list_knowledge(project_id: Optional[str] = None, role: Optional[str] = None,
                   kind: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Knowledge)
    if project_id:
        q = q.filter(Knowledge.project_id == project_id)
    if role:
        q = q.filter(Knowledge.role == role)
    if kind:
        q = q.filter(Knowledge.kind == kind)
    return [k.to_dict() for k in q.all()]

@app.post("/knowledge", status_code=201)
def create_knowledge(body: KnowledgeIn, db: Session = Depends(get_db)):
    validate_status(body.role, ROLE_KNOWLEDGE, field="role")
    validate_status(body.kind, KIND_KNOWLEDGE, field="kind")
    validate_status(body.source, SOURCE_KNOWLEDGE, field="source")
    fetch_or_404(db, Project, body.project_id)
    card = Knowledge(
        id=new_id("k"), project_id=body.project_id, title=body.title,
        role=body.role, kind=body.kind, source=body.source, md=body.md,
        md_updated_at=_now() if body.md else None,
    )
    db.add(card); db.commit()
    return card.to_dict()

@app.get("/knowledge/{knowledge_id}")
def get_knowledge(knowledge_id: str, db: Session = Depends(get_db)):
    return fetch_or_404(db, Knowledge, knowledge_id).to_dict()

@app.patch("/knowledge/{knowledge_id}")
def update_knowledge(knowledge_id: str, body: KnowledgePatch, db: Session = Depends(get_db)):
    validate_status(body.role, ROLE_KNOWLEDGE, field="role")
    validate_status(body.kind, KIND_KNOWLEDGE, field="kind")
    validate_status(body.source, SOURCE_KNOWLEDGE, field="source")
    card = fetch_or_404(db, Knowledge, knowledge_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    apply_md_timestamp(card, data)
    for k, v in data.items():
        setattr(card, k, v)
    db.commit()
    return card.to_dict()

@app.delete("/knowledge/{knowledge_id}")
def delete_knowledge(knowledge_id: str, db: Session = Depends(get_db)):
    db.delete(fetch_or_404(db, Knowledge, knowledge_id)); db.commit()
    return {"deleted": knowledge_id}


# ---------- SNAPSHOT ----------

@app.get("/state")
def full_state(db: Session = Depends(get_db)):
    return {
        "projects":  [p.to_dict() for p in db.query(Project).all()],
        "epics":     [e.to_dict() for e in db.query(Epic).all()],
        "stories":   [s.to_dict() for s in db.query(Story).all()],
        "tasks":     [t.to_dict() for t in db.query(Task).all()],
        "agents":    [a.to_dict() for a in db.query(Agent).all()],
        "knowledge": [k.to_dict() for k in db.query(Knowledge).all()],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("TABULA_PORT", "9955"))
    uvicorn.run(app, host="0.0.0.0", port=port)
