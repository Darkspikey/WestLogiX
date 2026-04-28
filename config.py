# config.py
import os

# ─── LLM Modell ────────────────────────────────────────────────────────────────
# Lokal (kostenlos, schwächer):     ollama / mistral
# Cloud (empfohlen für Produktion): openai / gpt-4o  ODER  anthropic / claude-sonnet-4-20250514
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")
MODEL_NAME     = os.getenv("MODEL_NAME",     "mistral")

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY",    "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─── Agent ─────────────────────────────────────────────────────────────────────
MAX_STEPS   = 8
TEMPERATURE = 0   # deterministisch → stabiles JSON

# ─── Persistenz ────────────────────────────────────────────────────────────────
MEMORY_FILE = "memory.json"
LOG_FILE    = "agent.log"

# ─── SAP EWM OData ─────────────────────────────────────────────────────────────
# EWM_MOCK = True  → Demo-Daten, kein SAP nötig
# EWM_MOCK = False → echter OData-Call gegen dein EWM-System
EWM_MOCK = os.getenv("EWM_MOCK", "true").lower() != "false"

# Dein lokaler EWM-Entwicklungsserver
EWM_ODATA_URL = os.getenv("EWM_ODATA_URL", "http://vhcala4hci:50000/sap/opu/odata/sap/")
EWM_USER      = os.getenv("EWM_USER", "")   # z.B. DEVELOPER oder BASISUSER
EWM_PASS      = os.getenv("EWM_PASS", "")

# EWM Service-Name – trag hier deinen SEGW-Service ein sobald du ihn angelegt hast
# Beispiel: "ZWL_SMART_PICK_SRV"
EWM_SERVICE   = os.getenv("EWM_SERVICE", "ZWL_SMART_PICK_SRV")
