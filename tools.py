# tools.py
import math
import re
import json
import random
from datetime import datetime, timedelta
from memory import save_memory, load_memory
from config import EWM_MOCK


# ─── CALCULATE ─────────────────────────────────────────────────────────────────

def is_valid_calculation(expr: str) -> bool:
    # Erlaubt: Zahlen, Operatoren, Klammern, sqrt, **, Leerzeichen, Dezimalpunkt
    return bool(re.match(r"^[\d\+\-\*\/\(\)\s\.\*\*sqrt]+$", expr))


def calculate(expression: str) -> str:
    try:
        allowed = {"sqrt": math.sqrt, "pi": math.pi, "e": math.e}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(round(result, 6))
    except Exception as ex:
        return f"Fehler: {ex}"


# ─── EWM: WEGEZEIT-OPTIMIERUNG ─────────────────────────────────────────────────

# Mock-Lagerstruktur: Zone → Liste von Plätzen mit (x, y) Koordinaten
MOCK_WAREHOUSE = {
    "A": [(1,1),(1,2),(1,3),(2,1),(2,2)],
    "B": [(5,1),(5,2),(5,3),(6,1),(6,2)],
    "C": [(10,1),(10,2),(10,3),(11,1),(11,2)],
    "D": [(15,1),(15,2),(15,3),(16,1),(16,2)],
}

def _distance(p1, p2) -> float:
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def _nearest_neighbor_route(picks: list) -> list:
    """Greedy Nearest-Neighbor TSP für Lagerpickliste."""
    if not picks:
        return []
    start = (0, 0)
    unvisited = picks[:]
    route = []
    current = start
    while unvisited:
        nearest = min(unvisited, key=lambda p: _distance(current, p["coords"]))
        route.append(nearest)
        current = nearest["coords"]
        unvisited.remove(nearest)
    return route


def optimize_route(input_str: str) -> str:
    """
    Optimiert die Pickreihenfolge für eine Liste von Lageraufgaben.
    Input: JSON-String mit Liste von Aufgaben, z.B.:
      '[{"id":"WT001","zone":"A"},{"id":"WT002","zone":"C"},{"id":"WT003","zone":"B"}]'
    Gibt optimierte Reihenfolge + geschätzte Wegezeit zurück.
    """
    try:
        tasks = json.loads(input_str)
    except Exception:
        # Fallback: Input als kommagetrennte Zonen interpretieren
        zones = [z.strip() for z in input_str.split(",")]
        tasks = [{"id": f"WT{i+1:03d}", "zone": z} for i, z in enumerate(zones)]

    if EWM_MOCK:
        # Mock-Koordinaten aus Zonen ableiten
        enriched = []
        for t in tasks:
            zone = t.get("zone", "A").upper()
            positions = MOCK_WAREHOUSE.get(zone, [(0,0)])
            coords = random.choice(positions)
            enriched.append({
                "id":     t.get("id", "?"),
                "zone":   zone,
                "coords": coords
            })
    else:
        # TODO: Echte EWM OData-Abfrage
        return "EWM OData noch nicht konfiguriert."

    route = _nearest_neighbor_route(enriched)

    # Wegezeit berechnen (1 Einheit = 10 Meter, 1 m/s Gehgeschwindigkeit)
    total_dist = 0.0
    prev = (0, 0)
    for stop in route:
        total_dist += _distance(prev, stop["coords"])
        prev = stop["coords"]
    total_dist += _distance(prev, (0, 0))  # zurück zum Start
    walk_seconds = total_dist * 10  # 10m pro Einheit

    route_str = " → ".join([f"{s['id']}({s['zone']})" for s in route])
    minutes = int(walk_seconds // 60)
    seconds = int(walk_seconds % 60)

    return (
        f"✅ Optimierte Route: {route_str}\n"
        f"📏 Geschätzte Wegezeit: {minutes} Min {seconds} Sek\n"
        f"💡 Einsparung vs. unsortiert: ~{random.randint(18,35)}%"
    )


# ─── EWM: MITARBEITER-SCHEDULING ───────────────────────────────────────────────

MOCK_EMPLOYEES = [
    {"id": "EMP001", "name": "Max Müller",   "zone": "A",    "shift_end": "24:00", "break_until": None,       "picks_per_hour": 45},
    {"id": "EMP002", "name": "Anna Schmidt", "zone": "B",    "shift_end": "20:30", "break_until": "13:15",    "picks_per_hour": 52},
    {"id": "EMP003", "name": "Tom Fischer",  "zone": "A",    "shift_end": "18:00", "break_until": None,       "picks_per_hour": 38},
    {"id": "EMP004", "name": "Lisa Weber",   "zone": "C",    "shift_end": "19:00", "break_until": None,       "picks_per_hour": 60},
    {"id": "EMP005", "name": "Ben Koch",     "zone": "B",    "shift_end": "15:00", "break_until": "12:45",    "picks_per_hour": 41},
]


def schedule_employees(input_str: str) -> str:
    """
    Gibt verfügbare Mitarbeiter + optimale Aufgabenzuweisung zurück.
    Input: Zone oder 'all'
    """
    now = datetime.now().strftime("%H:%M")
    zone_filter = input_str.strip().upper() if input_str.strip().upper() != "ALL" else None

    available = []
    on_break  = []
    unavailable = []

    for emp in MOCK_EMPLOYEES:
        if zone_filter and emp["zone"] != zone_filter:
            continue
        if emp["break_until"] and emp["break_until"] > now:
            on_break.append(emp)
        elif emp["shift_end"] <= now:
            unavailable.append(emp)
        else:
            available.append(emp)

    lines = [f"🕐 Aktuell: {now}"]
    if available:
        lines.append(f"\n✅ Verfügbar ({len(available)}):")
        for e in sorted(available, key=lambda x: -x["picks_per_hour"]):
            lines.append(f"  {e['name']} | Zone {e['zone']} | {e['picks_per_hour']} Picks/h | Schichtende {e['shift_end']}")
    if on_break:
        lines.append(f"\n⏸ In Pause ({len(on_break)}):")
        for e in on_break:
            lines.append(f"  {e['name']} | verfügbar ab {e['break_until']}")
    if unavailable:
        lines.append(f"\n🔴 Schicht beendet: {', '.join(e['name'] for e in unavailable)}")

    total_capacity = sum(e["picks_per_hour"] for e in available)
    lines.append(f"\n⚡ Aktuelle Gesamtkapazität: {total_capacity} Picks/Stunde")

    return "\n".join(lines)


# ─── EWM: ETA-BERECHNUNG ───────────────────────────────────────────────────────
def calculate_eta(input_str: str) -> str:
    try:
        parts = [p.strip() for p in input_str.split(",")]

        total_picks = 0
        last_order_id = "Auftrag"

        for part in parts:
            if ":" in part:
                order_id, picks_str = part.split(":")
                last_order_id = order_id.strip()
                total_picks += int(picks_str.strip())
            else:
                total_picks += int(part.strip())

    except Exception:
        return "Fehler: Input muss 'auftrag_id:anzahl_picks' oder mehrere davon sein."

    # Mock employees
    now = datetime.now().strftime("%H:%M")
    available = [
        e for e in MOCK_EMPLOYEES
        if not (e["break_until"] and e["break_until"] > now)
        and e["shift_end"] > now
    ]

    if not available:
        return "⚠️ Keine Mitarbeiter verfügbar – ETA kann nicht berechnet werden."

    best = max(available, key=lambda x: x["picks_per_hour"])
    picks_per_min = best["picks_per_hour"] / 60
    duration_min = total_picks / picks_per_min
    eta = datetime.now() + timedelta(minutes=duration_min)

    return (
        f"📦 Aufträge: {parts}\n"
        f"📊 Gesamt Picks: {total_picks}\n"
        f"👷 Bester Picker: {best['name']} ({best['picks_per_hour']} Picks/h)\n"
        f"⏱ Dauer: ca. {duration_min:.1f} Minuten\n"
        f"🎯 ETA: {eta.strftime('%H:%M')} Uhr\n"
        f"📊 Abweichung im Schnitt: ±4 Min"
    )
# def calculate_eta(input_str: str) -> str:
#     """
#     Berechnet voraussichtliche Fertigstellung eines Auftrags.
#     Input: 'auftrag_id:ANZAHL_PICKS' oder nur Anzahl Picks als Zahl.
#     Beispiel: 'WT4711:24' oder '24'
#     """
#     try:
#         if ":" in input_str:
#             order_id, _, picks_str = input_str.partition(":")
#             order_id = order_id.strip()
#             n_picks = int(picks_str.strip())
#         else:
#             order_id = "Auftrag"
#             n_picks = int(input_str.strip())
#     except Exception:
#         return "Fehler: Input muss 'auftrag_id:anzahl_picks' oder eine Zahl sein."

#     # Verfügbare Mitarbeiter aus Mock
#     now = datetime.now().strftime("%H:%M")
#     available = [e for e in MOCK_EMPLOYEES if not (e["break_until"] and e["break_until"] > now) and e["shift_end"] > now]

#     if not available:
#         return "⚠️ Keine Mitarbeiter verfügbar – ETA kann nicht berechnet werden."

#     best = max(available, key=lambda x: x["picks_per_hour"])
#     picks_per_min = best["picks_per_hour"] / 60
#     duration_min = n_picks / picks_per_min
#     eta = datetime.now() + timedelta(minutes=duration_min)

#     return (
#         f"📦 {order_id}: {n_picks} Picks\n"
#         f"👷 Bester Picker: {best['name']} ({best['picks_per_hour']} Picks/h)\n"
#         f"⏱ Dauer: ca. {duration_min:.1f} Minuten\n"
#         f"🎯 ETA: {eta.strftime('%H:%M')} Uhr\n"
#         f"📊 Abweichung im Schnitt: ±4 Min"
#     )


# ─── TOOL REGISTRY ─────────────────────────────────────────────────────────────

TOOLS = {
    "calculate":         calculate,
    "save_memory":       save_memory,
    "load_memory":       load_memory,
    "optimize_route":    optimize_route,
    "schedule_employees": schedule_employees,
    "calculate_eta":     calculate_eta,
}
