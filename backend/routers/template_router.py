"""
Şablon (Template) yönetimi router'ı.
Endpoint'ler: /me/templates, /me/templates/{id},
              /datasets/{id}/apply-template/{tid}
"""
from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.core.background_tasks import _apply_template_async
from backend.core.helpers import template_owned, dataset_owned
from backend.database import CleaningTemplate, Dataset, User, get_db

router = APIRouter()


# ── Pydantic modeller ────────────────────────────────────────────────────────

class Selection(BaseModel):
    category: str
    column: str
    method: str


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    selections: list[Selection]


# ── Endpoint'ler ─────────────────────────────────────────────────────────────

@router.get("/me/templates")
def list_templates(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(CleaningTemplate)
        .filter(CleaningTemplate.user_id == user.id)
        .order_by(CleaningTemplate.created_at.desc())
        .all()
    )
    out = []
    for r in rows:
        try:
            sel = json.loads(r.selections_json)
        except Exception:
            sel = []
        out.append({
            "id": r.id,
            "name": r.name,
            "selections_count": len(sel) if isinstance(sel, list) else 0,
        })
    return {"templates": out}


@router.post("/me/templates")
def save_template(
    body: TemplateCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = CleaningTemplate(
        user_id=user.id,
        name=body.name.strip(),
        selections_json=json.dumps([s.model_dump() for s in body.selections], ensure_ascii=False),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "name": t.name}


@router.delete("/me/templates/{template_id}")
def delete_template(
    template_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = template_owned(db, template_id, user)
    if not t:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı.")
    db.delete(t)
    db.commit()
    return {"ok": True}


@router.post("/datasets/{dataset_id}/apply-template/{template_id}")
def apply_template(
    dataset_id: int,
    template_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = template_owned(db, template_id, user)
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).with_for_update().first()
    if not t or not ds or ds.user_id != user.id:
        raise HTTPException(status_code=404, detail="Şablon veya veri seti bulunamadı.")
    if ds.status in ("processing", "analyzing"):
        raise HTTPException(status_code=400, detail="Veri seti şu an başka bir işlem tarafından işleniyor.")
    try:
        raw = json.loads(t.selections_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Şablon verisi okunamadı.")
    if not isinstance(raw, list):
        raise HTTPException(status_code=400, detail="Geçersiz şablon.")
    ds.status = "processing"
    db.commit()

    background_tasks.add_task(_apply_template_async, dataset_id, user.id, raw)
    return {"status": "processing", "message": "Şablon temizleme işlemi arka planda başlatıldı."}
