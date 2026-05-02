# api.py – WestLogiX FastAPI Backend
# Startet mit: python api.py
# Docs unter:  http://localhost:8000/docs

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os

from tools import (
    optimize_route,
    schedule_employees,
    calculate_eta,
    ewm_get_tasks,
    MOCK_EMPLOYEES,
)
from agent import run_agent

# ─── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="WestLogiX API",
    description="SAP EWM KI-Optimierung – Smart Pick Engine",
    version="0.2.0"
)

# CORS – erlaubt Dashboard (HTML) auf localhost den API-Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request/Response Models ───────────────────────────────────────────────────

class RouteRequest(BaseModel):
    zones: str  # z.B. "A, C, B, A" oder JSON-Array

class ETARequest(BaseModel):
    input: str  # z.B. "WT4711:24" oder "WT4711:20, WT4712:10"

class ScheduleRequest(BaseModel):
    zone: Optional[str] = "all"

class AgentRequest(BaseModel):
    message: str

# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "product": "WestLogiX Smart Pick Engine",
        "version": "0.2.0",
        "status": "running",
        "docs": "http://localhost:8000/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# ─── EWM Tasks ─────────────────────────────────────────────────────────────────

@app.get("/api/tasks")
def get_tasks():
    """Holt offene Lageraufgaben aus EWM (Mock oder Live)."""
    result = ewm_get_tasks()
    # Strukturiert zurückgeben
    lines = result.strip().split("\n")
    tasks = []
    for line in lines[1:]:  # erste Zeile ist Header
        line = line.strip()
        if line.startswith("TA"):
            parts = line.replace("TA ", "").split("|")
            if len(parts) >= 4:
                tasks.append({
                    "tanum":  parts[0].strip(),
                    "von":    parts[1].strip(),
                    "nach":   parts[2].strip(),
                    "matnr":  parts[3].strip() if len(parts) > 3 else "",
                    "menge":  parts[4].strip() if len(parts) > 4 else "",
                })
    return {"count": len(tasks), "tasks": tasks, "raw": result}

# ─── Route Optimierung ─────────────────────────────────────────────────────────

@app.post("/api/route/optimize")
def optimize(req: RouteRequest):
    """Optimiert Pick-Route für gegebene Zonen."""
    result = optimize_route(req.zones)
    lines = result.split("\n")
    return {
        "route":    lines[0].replace("✅ Optimierte Route: ", "") if lines else "",
        "wegezeit": lines[1].replace("📏 Geschätzte Wegezeit: ", "") if len(lines) > 1 else "",
        "einsparung": lines[2].replace("💡 Einsparung vs. unsortiert: ", "") if len(lines) > 2 else "",
        "raw": result
    }

# ─── Mitarbeiter ───────────────────────────────────────────────────────────────

@app.post("/api/employees/schedule")
def schedule(req: ScheduleRequest):
    """Gibt Mitarbeiter-Verfügbarkeit zurück."""
    result = schedule_employees(req.zone or "all")
    return {"raw": result}

@app.get("/api/employees")
def get_employees():
    """Gibt alle Mitarbeiter mit Status zurück."""
    from datetime import datetime
    now = datetime.now().strftime("%H:%M")
    employees = []
    for emp in MOCK_EMPLOYEES:
        if emp["break_until"] and emp["break_until"] > now:
            status = "pause"
        elif emp["shift_end"] <= now:
            status = "done"
        else:
            status = "available"
        employees.append({
            "id":           emp["id"],
            "name":         emp["name"],
            "zone":         emp["zone"],
            "shift_end":    emp["shift_end"],
            "break_until":  emp["break_until"],
            "picks_per_hour": emp["picks_per_hour"],
            "status":       status,
        })
    available_capacity = sum(
        e["picks_per_hour"] for e in employees if e["status"] == "available"
    )
    return {
        "employees": employees,
        "total": len(employees),
        "available": sum(1 for e in employees if e["status"] == "available"),
        "on_break": sum(1 for e in employees if e["status"] == "pause"),
        "capacity_per_hour": available_capacity,
    }

# ─── ETA ───────────────────────────────────────────────────────────────────────

@app.post("/api/eta")
def eta(req: ETARequest):
    """Berechnet ETA für Aufträge."""
    result = calculate_eta(req.input)
    return {"raw": result}

# ─── Dashboard Metriken (alles auf einmal) ─────────────────────────────────────

@app.get("/api/metrics")
def metrics():
    """Alle Dashboard-Metriken in einem Call – für das Live-Dashboard."""
    from datetime import datetime

    # Tasks
    tasks_raw = ewm_get_tasks()
    task_lines = [l for l in tasks_raw.split("\n") if l.strip().startswith("TA")]
    task_count = len(task_lines)

    # Employees
    emp_data = get_employees()

    # Route (Demo: feste Beispiel-Route)
    route_data = optimize(RouteRequest(zones="B, D, A, C, A, B, D, C, A, B"))

    # ETA
    eta1 = calculate_eta("WT4711:24")
    eta2 = calculate_eta("WT4712:18")
    eta3 = calculate_eta("WT4713:30")

    return {
        "timestamp": datetime.now().isoformat(),
        "tasks": {
            "open": task_count,
            "raw": tasks_raw
        },
        "employees": emp_data,
        "route": route_data,
        "eta": {
            "WT4711": eta1,
            "WT4712": eta2,
            "WT4713": eta3,
        },
        "savings_pct": route_data.get("einsparung", ""),
    }

# ─── AI Agent ──────────────────────────────────────────────────────────────────

@app.post("/api/agent")
def agent(req: AgentRequest):
    """Sendet eine Nachricht an den WestLogiX AI Agent."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Nachricht darf nicht leer sein.")
    result = run_agent(req.message)
    return {"response": result}

# ─── Start ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════╗
║       WestLogiX API  v0.2  –  FastAPI            ║
║  http://localhost:8000                           ║
║  http://localhost:8000/docs  (Swagger UI)        ║
╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
