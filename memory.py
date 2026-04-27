# memory.py
import json
import os
from datetime import datetime
from config import MEMORY_FILE


def _load_raw() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {"facts": {}, "history": []}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Migration: altes flaches Array → neues Format
    if isinstance(data, list):
        migrated = {"facts": {}, "history": []}
        for item in data:
            if isinstance(item, str) and ":" in item:
                k, _, v = item.partition(":")
                migrated["facts"][k.strip()] = v.strip()
        return migrated
    return data


def _save_raw(data: dict):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_memory(text: str) -> str:
    """
    Speichert einen Fakt. Format: 'key: value' → als Key-Value.
    Sonst als Eintrag mit Timestamp.
    """
    data = _load_raw()
    if ":" in text:
        key, _, value = text.partition(":")
        data["facts"][key.strip()] = value.strip()
        _save_raw(data)
        return f"✅ Gespeichert: {key.strip()} = {value.strip()}"
    else:
        entry = {"ts": datetime.now().isoformat(), "note": text}
        data["history"].append(entry)
        _save_raw(data)
        return f"✅ Notiz gespeichert: {text}"


def load_memory(_=None) -> str:
    """Gibt alle gespeicherten Fakten als lesbaren String zurück."""
    data = _load_raw()
    parts = []
    if data["facts"]:
        parts.append("📋 Fakten:")
        for k, v in data["facts"].items():
            parts.append(f"  {k}: {v}")
    if data["history"]:
        parts.append("📝 Notizen:")
        for entry in data["history"][-5:]:  # nur die letzten 5
            parts.append(f"  [{entry['ts'][:10]}] {entry['note']}")
    return "\n".join(parts) if parts else "Kein Memory vorhanden."


def get_facts() -> dict:
    return _load_raw()["facts"]
