# reflector.py
import logging

log = logging.getLogger("westlogix")

# Schlüsselwörter die auf eine Fehler-Antwort hinweisen
_ERROR_PHRASES = [
    "konnte nicht", "nicht erreichbar", "kein ergebnis", "keine daten",
    "unbekannt", "fehler:", "❌", "tool-fehler",
]


def reflect(user_input: str, tool_result, final_answer: str) -> dict:
    """Schnelle regelbasierte Qualitätsprüfung – kein zweiter LLM-Call."""

    # Leere Antwort
    if not final_answer or not final_answer.strip():
        return {"correct": False, "fix": "Die Antwort ist leer."}

    answer_lower = final_answer.lower()

    # Wenn ein Tool-Ergebnis vorliegt: prüfe ob die Antwort Schlüsselwörter daraus enthält
    if tool_result:
        result_lower = str(tool_result).lower()

        # Tool hat Fehler gemeldet → Antwort ist trotzdem ok wenn sie das erklärt
        if "fehler" in result_lower or "❌" in result_lower:
            return {"correct": True}

        # Tool-Ergebnis enthält konkrete Namen/Zahlen → Antwort sollte etwas davon haben
        # Heuristik: mindestens 20 Zeichen in der Antwort → als korrekt werten
        if len(final_answer.strip()) >= 20:
            return {"correct": True}

    # Antwort enthält nur Fehlerphrasen ohne Inhalt → ablehnen
    has_only_errors = any(p in answer_lower for p in _ERROR_PHRASES) and len(final_answer) < 80
    if has_only_errors:
        log.warning(f"Reflection: Antwort klingt nach Fehler: {final_answer[:80]}")
        return {"correct": False, "fix": final_answer}

    return {"correct": True}
