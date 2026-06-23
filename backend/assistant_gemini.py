"""Gemini (Google AI Studio) yardımcı asistan — API anahtarı yalnızca sunucu ortamında."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

from backend.environment import load_project_env

load_project_env()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Sen PrepWise adlı veri temizleme platformunun profesyonel, zeki ve yardımsever asistanısın.

Yanıt verirken şu kurallara kesinlikle uy:
- Asla Markdown formatı kullanma! Kalın yazı için ** veya * gibi yıldız işaretlerini KESİNLİKLE kullanma. Çünkü arayüzde bu yıldızlar çirkin görünüyor. Sadece düz metin (plain text) olarak yaz.
- Sadece alt satıra geçerek boşluk bırak. Başlık veya liste yapacaksan normal tire (-) veya rakam (1, 2, 3) kullan.
- Yanıtların son derece akıcı, kaliteli ve insan doğallığında olsun. Yapay zeka gibi robotik listeler sıralamak yerine doğal bir paragraf akışıyla anlat.
- PrepWise platformunda yapılabilecekler: CSV/Excel yükleme, yapay zeka analizleri, şablon kaydetme/uygulama, temiz veriyi indirme.
- PrepWise'da olmayan özellikler için dürüstçe "Bu özellik henüz yok" de.
- Sohbet akışını bozmayacak şekilde, kısa ama doyurucu bilgiler ver."""


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
    
    # Geçmişin şişmesini ve Rate Limit/Token hatalarını önlemek için yükü hafifletiyoruz.
    # Sadece en son 5 mesajı al.
    recent_msgs = messages[-5:]
    
    # Gemini API kuralı 1: İlk mesaj her zaman "user" olmalıdır.
    if recent_msgs and recent_msgs[0]["role"] != "user":
        recent_msgs = recent_msgs[1:]
        
    # Gemini API kuralı 2: Roller ('user', 'model') mutlaka ardışık olmalıdır!
    # Aksi takdirde API HTTP 400 döner. Arka arkaya gelen aynı rolleri filtreliyoruz.
    valid_msgs = []
    for msg in recent_msgs:
        if not valid_msgs:
            valid_msgs.append(msg)
        else:
            if valid_msgs[-1]["role"] == msg["role"]:
                # Aynı rol arka arkaya geldiyse eskiyi ez, yenisini (kullanıcının son yazdığını) al
                valid_msgs[-1] = msg
            else:
                valid_msgs.append(msg)
                
    # Her ihtimale karşı liste boş kalırsa veya tamamen hatalıysa son mesajı al
    if not valid_msgs:
        valid_msgs = messages[-1:]

    body: dict[str, Any] = {
        "contents": [{"role": m["role"], "parts": [{"text": m["text"]}]} for m in valid_msgs],
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
