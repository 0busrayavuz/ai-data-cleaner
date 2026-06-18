"""
Proje yönetimi router'ı.
Endpoint'ler: /projects, /projects/{id}, /projects/{id}/timeline
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import CleaningLog, Dataset, Project, QualityReport, User, get_db
from backend.core.helpers import project_owned

router = APIRouter()


# ── Pydantic modeller ────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


# ── Endpoint'ler ─────────────────────────────────────────────────────────────

@router.post("/projects")
def create_project(
    body: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = Project(user_id=user.id, name=body.name.strip(), description=body.description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name, "description": p.description}


@router.get("/projects")
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Project)
        .filter(Project.user_id == user.id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return {"projects": [{"id": r.id, "name": r.name, "description": r.description} for r in rows]}


@router.patch("/projects/{project_id}")
def update_project(
    project_id: int,
    body: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = project_owned(db, project_id, user)
    if not p:
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")
    if body.name is not None:
        p.name = body.name.strip()
    if body.description is not None:
        p.description = body.description
    db.commit()
    db.refresh(p)
    return {"id": project_id, "name": p.name, "description": p.description}


@router.get("/projects/{project_id}/timeline")
def project_timeline(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = project_owned(db, project_id, user)
    if not p:
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")

    dsets = (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id, Dataset.user_id == user.id)
        .all()
    )
    ids = [d.id for d in dsets]
    if not ids:
        return {"project_id": project_id, "project_name": p.name, "events": []}

    logs = (
        db.query(CleaningLog)
        .filter(CleaningLog.dataset_id.in_(ids))
        .order_by(CleaningLog.applied_at.asc())
        .all()
    )
    reports = (
        db.query(QualityReport)
        .filter(QualityReport.dataset_id.in_(ids))
        .order_by(QualityReport.created_at.asc())
        .all()
    )
    ds_map = {d.id: (d.original_filename or d.filename) for d in dsets}

    events = []
    for l in logs:
        events.append({
            "type": "operation",
            "at": l.applied_at.isoformat() if l.applied_at else None,
            "dataset_id": l.dataset_id,
            "dataset_file": ds_map.get(l.dataset_id, ""),
            "module": l.module,
            "column": l.column_name,
            "method": l.method,
            "detail": (l.details or "")[:500],
        })
    for r in reports:
        events.append({
            "id": r.id,
            "type": "quality_report",
            "at": r.created_at.isoformat() if r.created_at else None,
            "dataset_id": r.dataset_id,
            "dataset_file": ds_map.get(r.dataset_id, ""),
            "before_missing_pct": r.before_missing,
            "after_missing_pct": r.after_missing,
        })
    events.sort(key=lambda x: x.get("at") or "")
    return {"project_id": project_id, "project_name": p.name, "events": events}
