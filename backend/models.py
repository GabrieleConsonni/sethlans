"""
Tabula — Modelli ORM (SQLAlchemy 2.0)
=====================================
Schema dati condiviso tra l'app FastAPI (`tabula_server.py`) e le migrazioni
Alembic (`alembic/env.py`). Le tabelle non dichiarano lo schema: viene tradotto a
runtime su `tabula` tramite `schema_translate_map` (vedi `db.py` e `alembic/env.py`).
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Enum applicativi (validati nell'API)
STATUS_WORK = {"todo", "progress", "done"}      # epiche, storie, task
STATUS_AGENT = {"active", "idle"}               # agenti
PHASE_STORY = {"analysis", "ux", "design", "dev", "done"}  # fase del flusso (storie)
TYPE_PROJECT = {"jira", "internal"}             # progetto Jira o interno

# --- Knowledge cards (profilo progetto + KB del pre-training, vedi sethlans-onboard) ---
# role: a quale subagent/ambito serve la card; "general" = trasversale.
ROLE_KNOWLEDGE = {
    "general", "po", "architect", "ux", "tester",
    "frontend", "be-python", "be-java", "fullstack", "reviewer", "devops",
}
# kind: profile = specchio di CLAUDE.md/config; kb = conoscenza estratta; learnings = appresi a runtime.
KIND_KNOWLEDGE = {"profile", "kb", "learnings"}
# source: da dove proviene il contenuto.
SOURCE_KNOWLEDGE = {"claude_md", "confluence", "jira", "code", "manual"}


def new_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False, default="internal", server_default="internal")
    # chiave del progetto Jira (es. "ABC"); vuota per i progetti interni
    jira_key: Mapped[str] = mapped_column(String, default="", server_default="")
    # profilo consultabile (specchio di CLAUDE.md + pack), gestito da /sethlans-onboard
    md: Mapped[str] = mapped_column(Text, default="", server_default="")
    md_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # puntatori strutturati per-ruolo (Confluence space, design-system, ambienti di test, ...)
    config: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "jira_key": self.jira_key or "",
            "md": self.md or "",
            "md_updated_at": self.md_updated_at.isoformat() if self.md_updated_at else None,
            "config": self.config or {},
        }


class Epic(Base):
    __tablename__ = "epics"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    desc: Mapped[str] = mapped_column("desc", Text, default="", server_default="")
    status: Mapped[str] = mapped_column(String, nullable=False, default="todo", server_default="todo")
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    md: Mapped[str] = mapped_column(Text, default="", server_default="")
    md_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "desc": self.desc or "",
            "status": self.status,
            "project_id": self.project_id,
            "md": self.md or "",
            "md_updated_at": self.md_updated_at.isoformat() if self.md_updated_at else None,
        }


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    current_task: Mapped[str] = mapped_column(String, default="Inattivo", server_default="Inattivo")
    status: Mapped[str] = mapped_column(String, nullable=False, default="idle", server_default="idle")
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "current_task": self.current_task,
            "status": self.status,
            "tokens": self.tokens,
        }


class Story(Base):
    __tablename__ = "stories"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    desc: Mapped[str] = mapped_column("desc", Text, default="", server_default="")
    status: Mapped[str] = mapped_column(String, nullable=False, default="todo", server_default="todo")
    phase: Mapped[str] = mapped_column(String, nullable=False, default="analysis", server_default="analysis")
    epic_id: Mapped[str] = mapped_column(
        String, ForeignKey("epics.id", ondelete="CASCADE"), nullable=False
    )
    md: Mapped[str] = mapped_column(Text, default="", server_default="")
    md_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "desc": self.desc or "",
            "status": self.status,
            "phase": self.phase,
            "epic_id": self.epic_id,
            "md": self.md or "",
            "md_updated_at": self.md_updated_at.isoformat() if self.md_updated_at else None,
        }


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="todo", server_default="todo")
    story_id: Mapped[str] = mapped_column(
        String, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    md: Mapped[str] = mapped_column(Text, default="", server_default="")
    md_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "story_id": self.story_id,
            "agent_id": self.agent_id,
            "md": self.md or "",
            "md_updated_at": self.md_updated_at.isoformat() if self.md_updated_at else None,
        }


class Knowledge(Base):
    """Card di conoscenza di progetto (profilo + KB del pre-training).

    Appesa a un Project, indirizzata a un ruolo/subagent. Gli agenti la leggono
    a inizio task; il pre-training (`/sethlans-onboard`) la crea/aggiorna.
    """
    __tablename__ = "knowledge"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False, default="general", server_default="general")
    kind: Mapped[str] = mapped_column(String, nullable=False, default="kb", server_default="kb")
    title: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="manual", server_default="manual")
    md: Mapped[str] = mapped_column(Text, default="", server_default="")
    md_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "role": self.role,
            "kind": self.kind,
            "title": self.title,
            "source": self.source,
            "md": self.md or "",
            "md_updated_at": self.md_updated_at.isoformat() if self.md_updated_at else None,
        }
