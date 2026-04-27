# demo.py
from agent import run_agent
from demo_data import warehouse_data


def run_demo():

    print("\n📦 WESTLOGIX DEMO START\n")

    # 1. PROBLEM
    print("❗ Problem:")
    print("Viele Wege, schlechte Verteilung, ungenaue ETA\n")

    # 2. INPUT
    print("📊 Eingehende Daten:")
    print(warehouse_data)

    # 3. AI USE CASES

    print("\n🧠 Use Case 1: Wege optimieren")
    result1 = run_agent("Optimiere Wege im Lager basierend auf den Daten")
    print("➡️ Ergebnis:", result1)

    print("\n🧠 Use Case 2: Mitarbeiter Engpass erkennen")
    result2 = run_agent("Gibt es Engpässe bei Mitarbeitern?")
    print("➡️ Ergebnis:", result2)

    print("\n🧠 Use Case 3: ETA berechnen")
    result3 = run_agent("Berechne ETA für aktuelle Aufträge")
    print("➡️ Ergebnis:", result3)

    # 4. BUSINESS IMPACT
    print("\n💰 Impact:")
    print("- 20% weniger Wege")
    print("- 15% schnellere Auftragsbearbeitung")
    print("- bessere Planbarkeit")

    print("\n🚀 Fazit:")
    print("System kann live auf SAP EWM Daten laufen")


if __name__ == "__main__":
    run_demo()