# config.py
import os

# ─── Modell ────────────────────────────────────────────────────────────────────
# "ollama/mistral"  → lokal (schwächer, kostenlos)
# "openai/gpt-4o"   → OpenAI API
# "anthropic/claude-sonnet-4-20250514" → Claude (empfohlen für SAP-Logik)
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")   # ollama | openai | anthropic
MODEL_NAME     = os.getenv("MODEL_NAME",     "mistral")  # mistral | gpt-4o | claude-sonnet-4-20250514

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY",    "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─── Agent ─────────────────────────────────────────────────────────────────────
MAX_STEPS   = 8          # maximale Tool-Runden pro Query
TEMPERATURE = 0          # 0 = deterministisch (wichtig für JSON-Output)

# ─── Persistenz ────────────────────────────────────────────────────────────────
MEMORY_FILE = "memory.json"
LOG_FILE    = "agent.log"

# ─── EWM Mock-Daten (später durch echte OData-Calls ersetzen) ──────────────────
EWM_MOCK = True          # True = Dummy-Daten, False = echter OData-Endpoint
EWM_ODATA_URL = os.getenv("EWM_ODATA_URL", "http://localhost:8080/sap/opu/odata/sap/")
EWM_USER      = os.getenv("EWM_USER", "")
EWM_PASS      = os.getenv("EWM_PASS", "")
