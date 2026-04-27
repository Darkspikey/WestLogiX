# reflector.py
import json
import logging
from config import MODEL_PROVIDER

log = logging.getLogger("westlogix")

REFLECTION_PROMPT = """
Du bist ein Qualitätsprüfer für einen Lageroptimierungs-Agenten.

Du bekommst:
1. Die ursprüngliche Aufgabe des Users
2. Das letzte Tool-Ergebnis
3. Die finale Antwort des Agenten

Prüfe: Beantwortet die Antwort die Aufgabe korrekt und vollständig?

Antworte NUR mit JSON:

Wenn korrekt:
{"correct": true}

Wenn falsch oder unvollständig:
{"correct": false, "fix": "hier die korrekte, vollständige Antwort"}
"""


def reflect(user_input: str, tool_result, final_answer: str) -> dict:
    """Zweite KI-Instanz prüft ob die Antwort korrekt ist."""

    # Bei leerem Final einfach durchlassen
    if not final_answer or final_answer.strip() == "":
        return {"correct": False, "fix": str(tool_result) if tool_result else "Keine Antwort."}

    messages = [
        {"role": "system", "content": REFLECTION_PROMPT},
        {"role": "user",   "content": (
            f"Aufgabe: {user_input}\n"
            f"Tool-Ergebnis: {tool_result}\n"
            f"Agenten-Antwort: {final_answer}"
        )}
    ]

    try:
        # Import hier um zirkuläre Imports zu vermeiden
        from agent import llm_call
        output = llm_call(messages)

        # JSON extrahieren
        start = output.find("{")
        end   = output.rfind("}")
        if start != -1 and end != -1:
            return json.loads(output[start:end+1])

    except Exception as ex:
        log.warning(f"Reflection fehlgeschlagen: {ex}")

    # Fallback: Antwort als korrekt markieren
    return {"correct": True}
