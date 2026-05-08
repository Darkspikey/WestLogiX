# WestLogiX – Smart Pick Engine

> **KI-gestützte Optimierung für SAP EWM** – Wegezeiten, Picker-Planung, Echtzeit-ETA

[![Status](https://img.shields.io/badge/Status-MVP%20Live-brightgreen)]()
[![Version](https://img.shields.io/badge/Version-0.2-blue)]()
[![SAP](https://img.shields.io/badge/SAP-EWM-orange)]()

---

## Was ist WestLogiX?

WestLogiX ist ein KI-Agent der sich direkt in SAP EWM einklinkt und drei der häufigsten Lager-Probleme löst:

| Problem | Lösung | Impact |
|---------|--------|--------|
| Picker laufen kreuz und quer | Smart Route Engine (TSP) | **–62% Wegezeit** |
| Pausen unsichtbar für EWM | Picker Intelligence | **+20% Kapazität** |
| ETA = raten | ETA Engine | **±4 Min statt ±45 Min** |

---

## Schnellstart

```bash
pip install -r requirements.txt
```

### API Backend starten (empfohlen)
```bash
python api.py
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### Dashboard öffnen
```
dashboard/index.html → Doppelklick → Browser
# API muss laufen für Live-Daten
```

### CLI Agent
```bash
python main.py
```

### Demo (3 Use Cases)
```bash
python demo.py
```

---

## LLM Konfiguration

### Lokal mit Ollama (kostenlos)
```bash
ollama pull mistral        # oder qwen3.5:9b (besser)
python api.py
```

### OpenAI GPT-4o
```bash
set MODEL_PROVIDER=openai
set MODEL_NAME=gpt-4o
set OPENAI_API_KEY=sk-...
python api.py
```

### Anthropic Claude (empfohlen für Tool-Calls)
```bash
set MODEL_PROVIDER=anthropic
set MODEL_NAME=claude-sonnet-4-20250514
set ANTHROPIC_API_KEY=sk-ant-...
python api.py
```

> **Windows-Hinweis:** Immer `http://127.0.0.1:11434` für Ollama nutzen, nicht `localhost`

---

## Architektur

```
Dashboard (HTML)
    ↓ fetch() alle 30 Sek
FastAPI Backend (api.py · Port 8000)
    ↓
Agent Loop (agent.py)
    ├─ LLM-Adapter (Ollama / OpenAI / Anthropic)
    ├─ JSON-Extraktion (robust, 3 Strategien)
    ├─ Loop-Detection (tool+input Tupel)
    └─ Reflection Engine (reflector.py)
         ↓
Tools (tools.py)
    ├─ optimize_route        → TSP Wegeoptimierung
    ├─ schedule_employees    → Mitarbeiter-Verfügbarkeit
    ├─ calculate_eta         → Auftrags-ETA (Multi-Auftrag)
    ├─ ewm_get_tasks         → SAP EWM OData Connector
    ├─ calculate             → Mathe
    └─ save/load_memory      → Key-Value Persistenz
         ↓
SAP EWM OData
    └─ http://vhcala4hci:50000/sap/opu/odata/sap/
```

---

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `main.py` | CLI Entry Point |
| `api.py` | FastAPI Backend (9 Endpoints) |
| `agent.py` | Agent-Loop, LLM-Adapter, JSON-Parsing |
| `tools.py` | Route, Scheduling, ETA, EWM Connector |
| `schemy.py` | JSON-Schema für LLM Tool-Selection |
| `reflector.py` | Zweite KI-Instanz prüft Antworten |
| `memory.py` | Key-Value Persistenz (memory.json) |
| `config.py` | Zentrale Konfiguration |
| `demo.py` | Demo-Script (3 Use Cases) |
| `dashboard/index.html` | Live Dashboard mit Chat Widget |
| `CLAUDE.md` | Vollständiger Kontext für Claude Code |

---

## API Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/api/metrics` | Alle Dashboard-Metriken |
| GET | `/api/tasks` | EWM Lageraufgaben |
| GET | `/api/employees` | Mitarbeiter + Status |
| POST | `/api/route/optimize` | Route optimieren |
| POST | `/api/eta` | ETA berechnen |
| POST | `/api/agent` | AI Agent Chat |
| GET | `/docs` | Swagger UI |

---

## SAP EWM Live-Anbindung

Aktuell läuft WestLogiX mit Mock-Daten (`EWM_MOCK=True`).

Für echte SAP-Daten in `config.py`:

```python
EWM_MOCK      = False
EWM_SERVICE   = "ZWL_SMART_PICK_SRV"   # dein SEGW Service
EWM_USER      = "WESTLOGIX_API"
EWM_PASS      = "deinPasswort"
EWM_ODATA_URL = "http://vhcala4hci:50000/sap/opu/odata/sap/"
```

SAP-seitige Schritte: siehe `docs/WestLogiX_SAP_Leitfaden.docx`

---

## Roadmap

- [x] Smart Route Engine (TSP)
- [x] Picker Intelligence / Scheduling
- [x] ETA Engine (Multi-Auftrag)
- [x] FastAPI Backend
- [x] Live Dashboard
- [x] Agent Chat Widget
- [x] EWM OData Connector (Mock)
- [ ] SAP SEGW Service anlegen → EWM Live
- [ ] EWM Forecast (24h Prognose)
- [ ] Mitarbeiter-Performance Tracking
- [ ] EWM Rückschreiben (Warehouse Order)
- [ ] Multi-Lager Support
- [ ] Mobile App für Picker

---

## Business Case

```
Lager: 30 Picker · 8h Schicht · 25 €/h
Wegezeit-Einsparung: ~1.320 €/Tag
WestLogiX Starter: 800 €/Monat
→ Amortisation in 4,8 Arbeitstagen
→ Netto-Benefit: +3.400 €/Monat
```

---

*WestLogiX – AI Logistics Optimization · Made in Bavaria 🇩🇪*
