# WestLogiX AI Agent

SAP EWM Optimierungs-Agent – Basis für das WestLogiX Produkt.

## Setup

```bash
pip install -r requirements.txt
```

### Modell wählen (config.py oder Umgebungsvariablen)

**Lokal (kostenlos, schwächer):**
```bash
ollama pull mistral
python main.py
```

**OpenAI GPT-4o:**
```bash
export MODEL_PROVIDER=openai
export MODEL_NAME=gpt-4o
export OPENAI_API_KEY=sk-...
python main.py
```

**Anthropic Claude (empfohlen für SAP-Logik):**
```bash
export MODEL_PROVIDER=anthropic
export MODEL_NAME=claude-sonnet-4-20250514
export ANTHROPIC_API_KEY=sk-ant-...
python main.py
```

## Architektur

```
main.py          → CLI Entry Point
agent.py         → Agent-Loop, LLM-Adapter, JSON-Parsing
tools.py         → Tool-Implementierungen
  ├─ calculate          → Mathe
  ├─ save/load_memory   → Persistenz
  ├─ optimize_route     → Wegezeit-Optimierung (Nearest-Neighbor TSP)
  ├─ schedule_employees → Mitarbeiter-Verfügbarkeit
  └─ calculate_eta      → Auftrags-ETA
reflector.py     → Zweite KI-Instanz prüft Antwort
schemy.py        → JSON-Schema Enforcement
memory.py        → Key-Value Persistenz
config.py        → Zentrale Konfiguration
```

## Nächste Schritte

- [ ] Echte OData-Anbindung (EWM_MOCK = False in config.py)
- [ ] Web-Dashboard (FastAPI + React)
- [ ] Historische Daten → ML-Modell trainieren
- [ ] Multi-Lager Support
- [ ] Slack/Teams Alerts bei Engpässen
