# config.py
import os

# ─── LLM Modell ────────────────────────────────────────────────────────────────
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")
MODEL_NAME     = os.getenv("MODEL_NAME",     "Mistral")

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY",    "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─── Agent ─────────────────────────────────────────────────────────────────────
MAX_STEPS   = 8
TEMPERATURE = 0

# ─── Persistenz ────────────────────────────────────────────────────────────────
MEMORY_FILE = "memory.json"
LOG_FILE    = "agent.log"

# ─── Ollama Host (Windows Fix: 127.0.0.1 statt localhost) ──────────────────────
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# ─── SAP EWM OData ─────────────────────────────────────────────────────────────
EWM_MOCK      = os.getenv("EWM_MOCK", "true").lower() != "false"
EWM_ODATA_URL = os.getenv("EWM_ODATA_URL", "http://vhcala4hci:50000/sap/opu/odata/sap/")
EWM_USER      = os.getenv("EWM_USER", "")
EWM_PASS      = os.getenv("EWM_PASS", "")
EWM_SERVICE   = os.getenv("EWM_SERVICE", "ZWL_SMART_PICK_SRV")
