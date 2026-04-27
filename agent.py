# agent.py
import json
import re
import logging
from datetime import datetime
from config import (
    MODEL_PROVIDER, MODEL_NAME, MAX_STEPS, TEMPERATURE,
    LOG_FILE, ANTHROPIC_API_KEY, OPENAI_API_KEY
)
from tools import TOOLS, is_valid_calculation
from schemy import get_schema
from reflector import reflect

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("westlogix")


# ─── LLM-Adapter ───────────────────────────────────────────────────────────────

def llm_call(messages: list) -> str:
    """Einheitlicher LLM-Call – unterstützt Ollama, OpenAI, Anthropic."""

    if MODEL_PROVIDER == "ollama":
        import ollama
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            options={"temperature": TEMPERATURE}
        )
        return response["message"]["content"]

    elif MODEL_PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE
        )
        return response.choices[0].message.content

    elif MODEL_PROVIDER == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        # System-Nachricht separat herausfiltern
        system_msgs = [m["content"] for m in messages if m["role"] == "system"]
        user_msgs   = [m for m in messages if m["role"] != "system"]
        system_text = "\n\n".join(system_msgs)
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1024,
            system=system_text,
            messages=user_msgs,
            temperature=TEMPERATURE
        )
        return response.content[0].text

    else:
        raise ValueError(f"Unbekannter MODEL_PROVIDER: {MODEL_PROVIDER}")


# ─── JSON-Extraktion ────────────────────────────────────────────────────────────

def extract_json(text: str) -> dict | None:
    """
    Robuste JSON-Extraktion: findet das äußerste { ... } im Text.
    Funktioniert auch wenn das Modell Prosa davor/danach ausgibt.
    """
    # Strategie 1: direkt parsen
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Strategie 2: äußerstes { ... } extrahieren
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Strategie 3: Markdown-Codeblock entfernen
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    start = cleaned.find("{")
    end   = cleaned.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(cleaned[start:end+1])
        except Exception:
            pass

    log.warning(f"JSON-Extraktion fehlgeschlagen für: {text[:200]}")
    return None


def normalize_expression(expr: str) -> str:
    expr = expr.replace("Math.sqrt", "sqrt")
    expr = expr.replace("^", "**")
    return expr


# ─── Agent-Loop ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Du bist WestLogiX AI Agent – ein intelligenter Lageroptimierungs-Assistent für SAP EWM.

Deine Aufgaben:
- Wegezeiten optimieren
- Mitarbeiter-Verfügbarkeit planen
- Auftragsfälligkeiten (ETA) berechnen
- Fakten speichern und abrufen
- Berechnungen durchführen

WICHTIG: Antworte IMMER mit genau einem JSON-Objekt. Kein Text außerhalb.
"""


def run_agent(user_input: str) -> str:
    log.info(f"User: {user_input}")
    last_result = None
    reset_count = 0

    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "system",  "content": get_schema()},
        {"role": "user",    "content": user_input}
    ]

    for step in range(MAX_STEPS):
        log.info(f"--- Step {step+1}/{MAX_STEPS} ---")

        try:
            raw_output = llm_call(messages)
        except Exception as ex:
            log.error(f"LLM-Fehler: {ex}")
            return f"❌ LLM nicht erreichbar: {ex}"

        log.info(f"Raw output: {raw_output[:300]}")

        data = extract_json(raw_output)

        if not data:
            reset_count += 1
            if reset_count >= 3:
                return "❌ Agent konnte kein valides JSON erzeugen."
            log.warning("Kein JSON – sende Korrektur-Hint")
            messages.append({
                "role": "user",
                "content": "FEHLER: Deine Antwort war kein valides JSON. Antworte NUR mit einem JSON-Objekt."
            })
            continue

        thought = data.get("thought", "")
        tool    = data.get("tool",    "none")
        arg     = data.get("input",   "")
        final   = data.get("final",   "")

        log.info(f"Thought: {thought}")
        log.info(f"Tool: {tool}, Input: {arg}")

        print(f"\n{'─'*50}")
        print(f"🧠 {thought}")

        # ── FERTIG ──
        if tool == "none":
            reflection = reflect(user_input, last_result, final)
            log.info(f"Reflection: {reflection}")
            if reflection.get("correct"):
                log.info(f"Final answer: {final}")
                return final
            else:
                fixed = reflection.get("fix", final)
                log.info(f"Corrected answer: {fixed}")
                return fixed

        # ── TOOL-DISPATCH ──
        if tool not in TOOLS:
            messages.append({
                "role": "user",
                "content": f"FEHLER: Tool '{tool}' existiert nicht. Nutze: {list(TOOLS.keys())}"
            })
            continue

        # Spezial-Validierung für calculate
        if tool == "calculate":
            arg = normalize_expression(arg)
            if not is_valid_calculation(arg):
                messages.append({
                    "role": "user",
                    "content": f"FEHLER: Ausdruck '{arg}' enthält ungültige Zeichen."
                })
                continue

        try:
            result = TOOLS[tool](arg)
        except Exception as ex:
            result = f"Tool-Fehler: {ex}"

        log.info(f"Tool result: {result}")
        print(f"🔧 [{tool}] → {result}")

        # Loop-Erkennung
        if result == last_result:
            log.warning("Loop erkannt – breche ab")
            return str(result)
        last_result = result

        messages.append({
            "role": "user",
            "content": f"TOOL RESULT ({tool}):\n{result}"
        })

    log.error("Max Steps erreicht")
    return "❌ Maximale Schritte erreicht – Aufgabe zu komplex."
