"""
Gemini AI asistan router'ı.
Endpoint'ler: /assistant/chat
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.assistant_gemini import gemini_generate_reply
from backend.auth import get_current_user
from backend.database import User

router = APIRouter()


class AssistantChatMessage(BaseModel):
    role: Literal["user", "model"]
    text: str = Field(..., max_length=12000)


class AssistantChatBody(BaseModel):
    messages: list[AssistantChatMessage] = Field(..., min_length=1, max_length=40)


@router.post("/assistant/chat")
def assistant_chat(body: AssistantChatBody, _user: User = Depends(get_current_user)):
    """Gemini ile yardımcı asistan; API anahtarı sunucuda (GEMINI_API_KEY)."""
    msgs = [{"role": m.role, "text": m.text.strip()} for m in body.messages]
    if not msgs or not msgs[0]["text"]:
        raise HTTPException(status_code=400, detail="Geçerli bir mesaj gerekli.")
    if msgs[0]["role"] != "user":
        raise HTTPException(status_code=400, detail="Konuşma kullanıcı mesajı ile başlamalı.")
    try:
        reply = gemini_generate_reply(msgs)
    except ValueError:
        raise HTTPException(status_code=503, detail="AI asistan şu an kullanılamıyor. Lütfen sistem yöneticisiyle iletişime geçin.") from None
    except RuntimeError:
        raise HTTPException(status_code=502, detail="AI asistanından yanıt alınamadı. Lütfen sonra tekrar deneyin.") from None
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Asistan şu an yanıt veremedi. Lütfen sonra tekrar deneyin.",
        ) from None
    return {"reply": reply}
