# main.py
import sys
from agent import run_agent
from config import MODEL_PROVIDER, MODEL_NAME

BANNER = """
╔══════════════════════════════════════════════════════╗
║          WestLogiX AI Agent  v0.2                   ║
║    SAP EWM · Wegeoptimierung · Scheduling · ETA     ║
╚══════════════════════════════════════════════════════╝
"""

HELP = """
Beispiel-Fragen:
  → Optimiere Route für Zonen A, C, B, A
  → Wer ist in Zone B verfügbar?
  → Berechne ETA für WT4711 mit 30 Picks
  → Speichere: Kunde: Muster GmbH
  → Was weißt du über mich?
  → Berechne sqrt(144) + 5**2

Befehle: help | exit | quit
"""

def main():
    print(BANNER)
    print(f"Modell: {MODEL_PROVIDER}/{MODEL_NAME}")
    print(HELP)

    while True:
        try:
            user_input = input("Du: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nTschüss!")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Tschüss!")
            break
        if user_input.lower() == "help":
            print(HELP)
            continue

        print()
        answer = run_agent(user_input)
        print(f"\n✨ Agent: {answer}\n")


if __name__ == "__main__":
    main()
