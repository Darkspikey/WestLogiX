# WestLogiX – Claude Code Kontext

## Über den Entwickler
- **Name:** Kevin West
- **Standort:** Windischeschenbach, Bavaria
- **Job:** SAP EWM Consultant & Developer
- **Ziel:** WestLogiX als SaaS-Produkt skalieren → finanzielle Unabhängigkeit

## Projekt-Übersicht
**WestLogiX Smart Pick Engine** — KI-gestützter Agent für SAP EWM Optimierung.

**Core Value Proposition:**
- –62% Wegezeit durch TSP-Routenoptimierung
- ±4 Min ETA statt ±45 Min Raten
- +20% Pick-Kapazität ohne neue Mitarbeiter

## Projektpfad
```
C:\Users\kevin\AI-Agent\WESTLOGIX\WestLogiX\
```

## Dateistruktur
```
WestLogiX/
├── CLAUDE.md          ← diese Datei
├── main.py            ← CLI Entry Point
├── api.py             ← FastAPI Backend (Port 8000)
├── agent.py           ← Agent-Loop + LLM-Adapter
├── tools.py           ← Tool-Implementierungen
├── schemy.py          ← JSON-Schema für LLM
├── reflector.py       ← Zweite KI prüft Antworten
├── memory.py          ← Key-Value Persistenz
├── config.py          ← Zentrale Konfiguration
├── demo.py            ← Demo-Script (3 Use Cases)
├── memory.json        ← Persistierter Agent-Speicher
├── agent.log          ← Logging
└── dashboard/
    └── index.html     ← Live Dashboard (öffne im Browser)
```

## Architektur

```
Dashboard (HTML) → fetch() → FastAPI (api.py, Port 8000)
                                    ↓
                            Agent Loop (agent.py)
                                    ↓
                    Tools (tools.py) + LLM (config.py)
                                    ↓
                         SAP EWM OData (EWM_MOCK=True/False)
```

## Konfiguration (config.py)

```python
# Aktuell aktiv:
MODEL_PROVIDER = "ollama"
MODEL_NAME     = "mistral"      # oder "qwen3.5:9b" (besser)
OLLAMA_HOST    = "http://127.0.0.1:11434"  # Windows Fix!

# Für Produktion/Demos (besser):
MODEL_PROVIDER    = "anthropic"
MODEL_NAME        = "claude-sonnet-4-20250514"
ANTHROPIC_API_KEY = "sk-ant-..."

# SAP EWM:
EWM_MOCK    = True              # False = echter OData-Call
EWM_ODATA_URL = "http://vhcala4hci:50000/sap/opu/odata/sap/"
EWM_SERVICE   = "ZWL_SMART_PICK_SRV"
EWM_USER      = ""
EWM_PASS      = ""
```

## API Endpoints (api.py)

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/api/metrics` | Alle Dashboard-Metriken |
| GET | `/api/tasks` | EWM Lageraufgaben |
| GET | `/api/employees` | Mitarbeiter + Status |
| POST | `/api/route/optimize` | Route optimieren |
| POST | `/api/eta` | ETA berechnen |
| POST | `/api/agent` | AI Agent Chat |

## Verfügbare Tools (tools.py)

| Tool | Input | Beschreibung |
|------|-------|--------------|
| `calculate` | Rechenausdruck | Mathe |
| `save_memory` | "Key: Value" | Fakt speichern |
| `load_memory` | - | Alle Fakten laden |
| `optimize_route` | "A, C, B" oder JSON | TSP Routenoptimierung |
| `schedule_employees` | Zone oder "all" | Mitarbeiter-Verfügbarkeit |
| `calculate_eta` | "WT4711:24" | Auftrags-ETA |
| `ewm_get_tasks` | - | EWM Lageraufgaben |

## Bekannte Bugs / Fixes
- **Ollama Windows:** Immer `http://127.0.0.1:11434` nutzen, nicht `localhost`
- **Mistral Loop:** Loop-Detection läuft auf `(tool, input)` Tupel — nicht auf Result
- **calculate_eta:** Robuster Parser `_parse_eta_input()` — versteht alle LLM-Formate
- **schedule_employees:** None-safe — leerer Input → "all"
- **optimize_route:** String-Array `["Zone1"]` wird automatisch normalisiert

## Starten

```bash
# API Backend (Terminal 1):
cd C:\Users\kevin\AI-Agent\WESTLOGIX\WestLogiX
python api.py
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger)

# CLI Agent (Terminal 2):
python main.py

# Demo (Terminal 2):
python demo.py

# Dashboard:
# Öffne dashboard/index.html im Browser
# (API muss laufen für Live-Daten)

# Ollama (falls nötig, eigenes Terminal):
# Läuft normalerweise automatisch im Hintergrund
# Test: ollama run mistral "Hallo"
```

## Abhängigkeiten installieren

```bash
pip install fastapi uvicorn requests ollama openai anthropic
```

## SAP EWM Live-Anbindung (TODO)

Schritte für echten EWM-Connect (EWM_MOCK=False):

1. **SEGW:** Projekt `ZWL_SMART_PICK_SRV` anlegen
2. **Entity Type:** `WarehouseTask` mit Properties (Tanum, Vlpla, Nlpla, Matnr, Menge...)
3. **DPC Extension:** `WAREHOUSETA_SKSET_GET_ENTITYSET` → SELECT auf `/SCWM/ORDIM_C`
4. **Service registrieren:** `/IWFND/MAINT_SERVICE`
5. **User:** SU01 → `WESTLOGIX_API` (Systembenutzer)
6. **Config:** `EWM_MOCK=False`, Service-Name, User, Passwort eintragen
7. **Test:** `http://vhcala4hci:50000/sap/opu/odata/sap/ZWL_SMART_PICK_SRV/$metadata`

## Business Context

- **Zielkunden:** Lager mit SAP EWM, 10-100+ Picker
- **Pricing:** Starter 800€/Mon · Professional 1.500€/Mon · Enterprise Custom
- **ROI:** 4,8 Tage Amortisation bei 30 Pickern
- **Status:** MVP fertig, Mock-Daten, erster Pilot-Termin am 18. Mai (neoimpulse GmbH)
- **LinkedIn:** Post live, 1.661 Impressionen, 2 Termine generiert

## Coding-Stil Präferenzen
- Deutsch in Kommentaren und Logs
- Immer Syntax-Check nach Änderungen: `python -m py_compile datei.py`
- Robustes Error-Handling — nie crashen, immer sinnvolle Fehlermeldung
- Deterministisch wo möglich — kein `random` in Business-Logik
- Config-Werte immer aus `config.py`, nie hardcoded

## Nächste Schritte
- [ ] Claude/GPT-4o statt Mistral als Default (bessere Tool-Calls)
- [ ] SAP EWM SEGW Service anlegen (Leitfaden liegt vor)
- [ ] Dashboard Screenshot für Demo-Slide einfügen
- [ ] Nebengewerbe anmelden
- [ ] neoimpulse Pitch am 18. Mai
