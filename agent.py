# agent.py
import json
import re
import logging
from config import (
    MODEL_PROVIDER, MODEL_NAME, MAX_STEPS, TEMPERATURE,
    LOG_FILE, ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA_HOST
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
    if MODEL_PROVIDER == "ollama":
        import urllib.request, json as _json
        # Direkter HTTP Call - kein ollama Package nötig
        host = "http://127.0.0.1:11434"  # hardcoded für maximale Stabilität
        payload = _json.dumps({
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {"temperature": TEMPERATURE}
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{host}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return _json.loads(resp.read())["message"]["content"]

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
        system_msgs = [m["content"] for m in messages if m["role"] == "system"]
        user_msgs   = [m for m in messages if m["role"] != "system"]
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1024,
            system="\n\n".join(system_msgs),
            messages=user_msgs,
            temperature=TEMPERATURE
        )
        return response.content[0].text

    else:
        raise ValueError(f"Unbekannter MODEL_PROVIDER: {MODEL_PROVIDER}")


# ─── JSON-Extraktion ────────────────────────────────────────────────────────────

def extract_json(text: str) -> dict | None:
    # Strategie 1: direkt
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Strategie 2: äußerstes { ... }
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass

    # Strategie 3: Markdown-Backticks entfernen
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    start = cleaned.find("{")
    end   = cleaned.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(cleaned[start:end+1])
        except Exception:
            pass

    log.warning(f"JSON-Extraktion fehlgeschlagen: {text[:200]}")
    return None


def normalize_expression(expr: str) -> str:
    expr = expr.replace("Math.sqrt", "sqrt")
    expr = expr.replace("^", "**")
    return expr


# ─── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Du bist WestLogiX AI Agent – ein intelligenter Lageroptimierungs-Assistent für SAP EWM.

Deine Aufgaben:
- Wegezeiten optimieren
- Mitarbeiter-Verfügbarkeit planen
- Auftragsfälligkeiten (ETA) berechnen
- Fakten speichern und abrufen
- Berechnungen durchführen

WICHTIGSTE REGELN:
1. Antworte IMMER mit genau einem JSON-Objekt. Kein Text außerhalb.
2. Bei Begrüßungen oder einfachen Fragen ("Hallo", "Wie heiße ich?") → sofort tool="none" + final setzen.
3. Rufe NIEMALS dasselbe Tool zweimal hintereinander mit identischem Input auf.
4. Antworte immer auf Deutsch.
"""


# ─── Agent-Loop ─────────────────────────────────────────────────────────────────

def run_agent(user_input: str) -> str:
    log.info(f"User: {user_input}")

    # Loop-Detection: (tool, input) Tupel – nicht nur Result
    last_tool_call = None
    reset_count    = 0

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": get_schema()},
        {"role": "user",   "content": user_input}
    ]

    for step in range(MAX_STEPS):
        log.info(f"--- Step {step+1}/{MAX_STEPS} ---")

        try:
            raw_output = llm_call(messages)
        except Exception as ex:
            log.error(f"LLM-Fehler: {ex}")
            return f"❌ LLM nicht erreichbar: {ex}"

        log.info(f"Raw: {raw_output[:300]}")

        data = extract_json(raw_output)

        if not data:
            reset_count += 1
            if reset_count >= 3:
                return "❌ Agent konnte kein valides JSON erzeugen."
            messages.append({
                "role": "user",
                "content": "FEHLER: Keine valide JSON-Antwort. Antworte NUR mit einem JSON-Objekt, kein Text davor/danach."
            })
            continue

        thought = data.get("thought", "")
        tool    = data.get("tool",    "none")
        arg     = str(data.get("input", "")).strip()
        final   = str(data.get("final", "")).strip()

        log.info(f"Thought: {thought} | Tool: {tool} | Input: {arg[:80]}")
        print(f"\n{'─'*50}")
        print(f"🧠 {thought}")

        # ── FERTIG ──
        if tool == "none":
            if not final or final.lower() in ("none", "null"):
                messages.append({
                    "role": "user",
                    "content": "Du hast tool=none gesetzt aber 'final' ist leer oder ungültig ('none'/'null'). Schreibe jetzt eine vollständige Antwort in 'final'."
                })
                continue
            reflection = reflect(user_input, None, final)
            log.info(f"Reflection: {reflection}")
            return reflection.get("fix", final) if not reflection.get("correct") else final

        # ── UNBEKANNTES TOOL ──
        if tool not in TOOLS:
            messages.append({
                "role": "user",
                "content": f"FEHLER: Tool '{tool}' existiert nicht. Verfügbare Tools: {list(TOOLS.keys())}"
            })
            continue

        # ── LOOP-DETECTION: (tool, input) Paar ──
        current_call = (tool, arg)
        if current_call == last_tool_call:
            log.warning(f"Loop bei {tool}({arg[:40]}) – erzwinge Abschluss")
            messages.append({
                "role": "user",
                "content": "Du rufst dasselbe Tool mit identischem Input nochmals auf. Nutze jetzt tool='none' und schreibe deine finale Antwort in 'final'."
            })
            continue
        last_tool_call = current_call

        # ── Validierung calculate ──
        if tool == "calculate":
            arg = normalize_expression(arg)
            if not is_valid_calculation(arg):
                messages.append({
                    "role": "user",
                    "content": f"FEHLER: '{arg}' enthält ungültige Zeichen. Nur Zahlen, +,-,*,/,(,),sqrt,** erlaubt."
                })
                continue

        # ── Tool ausführen ──
        try:
            result = TOOLS[tool](arg if arg else None)
        except Exception as ex:
            result = f"Tool-Fehler: {ex}"

        log.info(f"Tool result: {str(result)[:200]}")
        print(f"🔧 [{tool}] → {result}")

        messages.append({
            "role": "user",
            "content": (
                f"TOOL RESULT ({tool}):\n{result}\n\n"
                "Beantworte jetzt die ursprüngliche Frage des Users basierend auf diesem Ergebnis. "
                "Setze tool='none' und schreibe deine Antwort in 'final'."
            )
        })

    log.error("Max Steps erreicht")
    return "❌ Maximale Schritte erreicht."
