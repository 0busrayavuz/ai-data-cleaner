"""Gemini (Google AI Studio) yardımcı asistan — API anahtarı yalnızca sunucu ortamında."""

from __future__ import annotations

import os
from typing import Any

import requests

from backend.environment import load_project_env

load_project_env()

SYSTEM_PROMPT = """Sen VeriTemiz AI adlı veri temizleme ve özellik mühendisliği web uygulamasının yardımcı asistanısın.
Kullanıcıya Türkçe, kısa ve net yanıtlar ver. Uydurma: platformda olmayan özellikleri varmış gibi anlatma.
Konular: CSV/Excel yükleme, analiz önerileri, eksik değer/aykırı tip düzeltmeleri, şablonlar, proje paneli, indirme.
Bilmediğin bir şey olursa dürüstçe söyle ve kullanıcıyı uygulama arayüzüne yönlendir."""


def _api_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()


def _model_id() -> str:
    return (os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash-lite").strip()


def gemini_generate_reply(messages: list[dict[str, str]]) -> str:
    """
    messages: [{"role": "user"|"model", "text": "..."}, ...] — ilk rol user olmalı.
    """
    key = _api_key()
    if not key:
        raise ValueError("GEMINI_API_KEY (veya GOOGLE_API_KEY) sunucu ortamında tanımlı değil.")

    model = _model_id()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body: dict[str, Any] = {
        "contents": [{"role": m["role"], "parts": [{"text": m["text"]}]} for m in messages],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {"temperature": 0.65, "maxOutputTokens": 1024},
    }
    resp = requests.post(url, params={"key": key}, json=body, timeout=90)
    if resp.status_code >= 400:
        snippet = (resp.text or "")[:600]
        raise RuntimeError(f"Gemini HTTP {resp.status_code}: {snippet}")

    data = resp.json()
    cands = data.get("candidates") or []
    if not cands:
        err = data.get("error", {}).get("message") or data.get("promptFeedback") or "Aday yanıt yok"
        raise RuntimeError(str(err)[:500])

    finish = (cands[0].get("finishReason") or "").upper()
    if finish in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT"):
        raise RuntimeError("Güvenlik filtresi nedeniyle yanıt üretilemedi. Sorunuzu yeniden ifade etmeyi deneyin.")

    parts = (cands[0].get("content") or {}).get("parts") or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
    out = "".join(texts).strip()
    return out or "Yanıt boş geldi; lütfen tekrar deneyin."
