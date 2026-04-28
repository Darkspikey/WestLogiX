# tools.py
import math
import re
import json
import requests
from datetime import datetime, timedelta
from memory import save_memory, load_memory
from config import EWM_MOCK, EWM_ODATA_URL, EWM_USER, EWM_PASS, EWM_SERVICE


# ─── CALCULATE ─────────────────────────────────────────────────────────────────

def is_valid_calculation(expr: str) -> bool:
    return bool(re.match(r"^[\d\+\-\*\/\(\)\s\.\*\*sqrt]+$", expr))


def calculate(expression: str) -> str:
    try:
        allowed = {"sqrt": math.sqrt, "pi": math.pi, "e": math.e}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(round(result, 6))
    except Exception as ex:
        return f"Fehler: {ex}"


# ─── EWM: WEGEZEIT-OPTIMIERUNG ─────────────────────────────────────────────────

MOCK_WAREHOUSE = {
    "A": [(1,1),(1,2),(1,3),(2,1),(2,2)],
    "B": [(5,1),(5,2),(5,3),(6,1),(6,2)],
    "C": [(10,1),(10,2),(10,3),(11,1),(11,2)],
    "D": [(15,1),(15,2),(15,3),(16,1),(16,2)],
}

def _distance(p1, p2) -> float:
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def _nearest_neighbor_route(picks: list) -> list:
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
    try:
        tasks = json.loads(input_str)
    except Exception:
        zones = [z.strip() for z in input_str.split(",")]
        tasks = [{"id": f"WT{i+1:03d}", "zone": z} for i, z in enumerate(zones)]

    if EWM_MOCK:
        enriched = []
        for t in tasks:
            zone = t.get("zone", "A").upper()
            positions = MOCK_WAREHOUSE.get(zone, [(0,0)])
            # Deterministisch: hash statt random
            idx = hash(t.get("id", "")) % len(positions)
            enriched.append({"id": t.get("id","?"), "zone": zone, "coords": positions[idx]})
    else:
        return ewm_get_tasks("optimize")

    optimized = _nearest_neighbor_route(enriched)

    # Original-Distanz (unoptimiert)
    orig_dist, prev = 0.0, (0,0)
    for s in enriched:
        orig_dist += _distance(prev, s["coords"]); prev = s["coords"]
    orig_dist += _distance(prev, (0,0))

    # Optimierte Distanz
    opt_dist, prev = 0.0, (0,0)
    for s in optimized:
        opt_dist += _distance(prev, s["coords"]); prev = s["coords"]
    opt_dist += _distance(prev, (0,0))

    walk_seconds = opt_dist * 10
    minutes = int(walk_seconds // 60)
    seconds = int(walk_seconds % 60)
    savings = round((1 - opt_dist / orig_dist) * 100, 1) if orig_dist > 0 else 0

    route_str = " → ".join([f"{s['id']}({s['zone']})" for s in optimized])
    return (
        f"✅ Optimierte Route: {route_str}\n"
        f"📏 Geschätzte Wegezeit: {minutes} Min {seconds} Sek\n"
        f"💡 Einsparung vs. unsortiert: {savings}%"
    )


# ─── EWM: MITARBEITER-SCHEDULING ───────────────────────────────────────────────

# HINWEIS: shift_end niemals "24:00" – Python "%H:%M" kennt nur bis "23:59"
MOCK_EMPLOYEES = [
    {"id": "EMP001", "name": "Max Müller",   "zone": "A", "shift_end": "23:59", "break_until": None,    "picks_per_hour": 45},
    {"id": "EMP002", "name": "Anna Schmidt", "zone": "B", "shift_end": "20:30", "break_until": "13:15", "picks_per_hour": 52},
    {"id": "EMP003", "name": "Tom Fischer",  "zone": "A", "shift_end": "18:00", "break_until": None,    "picks_per_hour": 38},
    {"id": "EMP004", "name": "Lisa Weber",   "zone": "C", "shift_end": "19:00", "break_until": None,    "picks_per_hour": 60},
    {"id": "EMP005", "name": "Ben Koch",     "zone": "B", "shift_end": "15:00", "break_until": None,    "picks_per_hour": 41},
]


def schedule_employees(input_str: str) -> str:
    now = datetime.now().strftime("%H:%M")
    zone_filter = input_str.strip().upper() if input_str.strip().upper() not in ("ALL", "") else None

    available, on_break, unavailable = [], [], []

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
    if not available and not on_break and not unavailable:
        lines.append("Keine Mitarbeiter für diese Zone gefunden.")

    total_capacity = sum(e["picks_per_hour"] for e in available)
    lines.append(f"\n⚡ Aktuelle Gesamtkapazität: {total_capacity} Picks/Stunde")
    return "\n".join(lines)


# ─── EWM: ETA-BERECHNUNG ───────────────────────────────────────────────────────

def _parse_eta_input(raw: str):
    """
    Parst alle Formate die LLMs liefern können:
      "WT4711:30"               -> [("WT4711", 30)]
      "WT4711:20, WT4712:10"    -> [("WT4711", 20), ("WT4712", 10)]   ← dein Multi-Auftrag
      "WT4711 mit 30 Picks"     -> [("WT4711", 30)]
      "30 Picks" / "30"         -> [("Auftrag", 30)]
    """
    results = []
    parts = [p.strip() for p in raw.split(",")]

    for part in parts:
        if not part:
            continue
        if ":" in part:
            # Standard-Format: ID:Anzahl
            left, _, right = part.partition(":")
            order_match = re.search(r"[A-Za-z]{1,4}\d{3,}", left)
            order_id = order_match.group(0).upper() if order_match else left.strip()
            nums = re.findall(r"\d+", right)
            if nums:
                results.append((order_id, int(nums[0])))
        else:
            # Freitext: Zahl extrahieren
            order_match = re.search(r"\b([A-Za-z]{1,4}\d{3,})\b", part)
            order_id = order_match.group(1).upper() if order_match else "Auftrag"
            nums = [int(n) for n in re.findall(r"\d+", part) if int(n) < 10000]
            if nums:
                results.append((order_id, nums[-1]))

    if not results:
        raise ValueError("Keine Picks-Anzahl erkannt")
    return results


def calculate_eta(input_str: str) -> str:
    try:
        parsed = _parse_eta_input(input_str)
    except Exception:
        return "Fehler: Konnte keine Picks-Anzahl erkennen. Beispiel: 'WT4711:30' oder 'WT4711:20, WT4712:10'"

    total_picks = sum(p for _, p in parsed)
    order_ids   = [o for o, _ in parsed]

    now = datetime.now().strftime("%H:%M")
    available = [e for e in MOCK_EMPLOYEES
                 if not (e["break_until"] and e["break_until"] > now)
                 and e["shift_end"] > now]

    if not available:
        return "⚠️ Keine Mitarbeiter verfügbar – ETA kann nicht berechnet werden."

    best = max(available, key=lambda x: x["picks_per_hour"])
    duration_min = total_picks / (best["picks_per_hour"] / 60)
    eta = datetime.now() + timedelta(minutes=duration_min)

    auftrag_str = ", ".join(order_ids) if len(order_ids) > 1 else order_ids[0]
    return (
        f"📦 Auftrag/Aufträge: {auftrag_str}\n"
        f"📊 Gesamt Picks: {total_picks}\n"
        f"👷 Bester Picker: {best['name']} ({best['picks_per_hour']} Picks/h)\n"
        f"⏱ Dauer: ca. {duration_min:.1f} Minuten\n"
        f"🎯 ETA: {eta.strftime('%H:%M')} Uhr\n"
        f"📊 Abweichung im Schnitt: ±4 Min"
    )


# ─── EWM: ODATA CONNECTOR ──────────────────────────────────────────────────────

def ewm_get_tasks(_=None) -> str:
    """
    Holt offene Lageraufgaben aus SAP EWM via OData.
    URL: http://vhcala4hci:50000/sap/opu/odata/sap/<EWM_SERVICE>/WarehouseTaskSet
    EWM_MOCK=True  → Demo-Daten
    EWM_MOCK=False → echter Call (EWM_USER + EWM_PASS in config/env setzen)
    """
    if EWM_MOCK:
        tasks = [
            {"Tanum": "0000001001", "Vlpla": "A-01-01", "Nlpla": "GI-ZONE", "Matnr": "MAT-001", "Menge": 5.0,  "Meins": "ST"},
            {"Tanum": "0000001002", "Vlpla": "B-03-02", "Nlpla": "GI-ZONE", "Matnr": "MAT-047", "Menge": 12.0, "Meins": "ST"},
            {"Tanum": "0000001003", "Vlpla": "C-02-05", "Nlpla": "GI-ZONE", "Matnr": "MAT-112", "Menge": 3.0,  "Meins": "KG"},
            {"Tanum": "0000001004", "Vlpla": "GR-ZONE", "Nlpla": "D-01-01", "Matnr": "MAT-033", "Menge": 8.0,  "Meins": "ST"},
        ]
        lines = [f"📋 Offene Lageraufgaben ({len(tasks)} Tasks) [DEMO]:"]
        for t in tasks:
            lines.append(f"  TA {t['Tanum']} | {t['Vlpla']} → {t['Nlpla']} | {t['Matnr']} | {t['Menge']} {t['Meins']}")
        return "\n".join(lines)

    # ── Echter EWM OData Call ──
    url = f"{EWM_ODATA_URL.rstrip('/')}/{EWM_SERVICE}/WarehouseTaskSet?$format=json&$top=20&$filter=Tostat eq 'A'"
    try:
        resp = requests.get(
            url,
            auth=(EWM_USER, EWM_PASS),
            timeout=10,
            headers={"Accept": "application/json", "sap-client": "100"}
        )
        resp.raise_for_status()
        tasks = resp.json().get("d", {}).get("results", [])

        if not tasks:
            return "ℹ️ Keine offenen Lageraufgaben gefunden."

        lines = [f"📋 Offene Lageraufgaben aus EWM ({len(tasks)} Tasks):"]
        for t in tasks:
            lines.append(
                f"  TA {t.get('Tanum','?')} | {t.get('Vlpla','?')} → {t.get('Nlpla','?')} "
                f"| {t.get('Matnr','?')} | {t.get('Menge','?')} {t.get('Meins','')}"
            )
        return "\n".join(lines)

    except requests.exceptions.ConnectionError:
        return f"❌ EWM nicht erreichbar: {url}\n→ Prüfe ob du im richtigen Netzwerk/VPN bist."
    except requests.exceptions.HTTPError as e:
        return f"❌ HTTP Fehler {e.response.status_code}: {e}\n→ Prüfe EWM_SERVICE, EWM_USER, EWM_PASS in config.py"
    except Exception as ex:
        return f"❌ Fehler: {ex}"


# ─── TOOL REGISTRY ─────────────────────────────────────────────────────────────

TOOLS = {
    "calculate":          calculate,
    "save_memory":        save_memory,
    "load_memory":        load_memory,
    "optimize_route":     optimize_route,
    "schedule_employees": schedule_employees,
    "calculate_eta":      calculate_eta,
    "ewm_get_tasks":      ewm_get_tasks,
}
