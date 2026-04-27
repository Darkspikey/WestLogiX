# schemy.py

def get_schema() -> str:
    return """
Du MUSST EXAKT EIN JSON-Objekt zurückgeben. Kein Text davor oder danach.

VERFÜGBARE TOOLS:
- calculate          → Rechenausdruck, z.B. "sqrt(144) + 5**2"
- save_memory        → Fakt speichern, z.B. "Kunde: Muster GmbH" oder freier Text
- load_memory        → Kein Input nötig → gibt alle gespeicherten Fakten zurück
- optimize_route     → JSON-Array mit Lageraufgaben, z.B. '[{"id":"WT001","zone":"A"},{"id":"WT002","zone":"C"}]'
                       oder kommagetrennte Zonen: "A, C, B, A"
- schedule_employees → Zone (A/B/C/D) oder "all" → zeigt Verfügbarkeit aller Mitarbeiter
- calculate_eta      → "auftrag_id:anzahl_picks", z.B. "WT4711:24" oder einfach "24"
- none               → wenn die Antwort fertig ist

PFLICHTFELDER:
{
  "thought": "Kurze Begründung was du jetzt tust",
  "tool": "einer der oben genannten Tool-Namen oder none",
  "input": "Eingabe für das Tool (leer lassen wenn tool=none)",
  "final": "Abschlussantwort an den User (nur setzen wenn tool=none)"
}

REGELN:
- Immer erst denken (thought), dann handeln (tool)
- Niemals mehrere JSON-Objekte
- Bei tool=none MUSS final gesetzt sein
- Bei tool≠none MUSS input gesetzt sein
"""
