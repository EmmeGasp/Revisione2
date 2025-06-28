from portfolio_manager import PortfolioManager
import sys

def main():
    print("=== MIGRAZIONE DATI PORTAFOGLI (enhanced_certificates.json -> portfolios.json/positions.json) ===")
    # Permetti di passare un percorso custom come argomento
    old_path = None
    if len(sys.argv) > 1:
        old_path = sys.argv[1]
        print(f"Percorso file da migrare specificato: {old_path}")
    else:
        print("Nessun percorso specificato, uso default.")

    try:
        portfolio_manager = PortfolioManager()
        result = portfolio_manager.migrate_from_old_enhanced_certificates(old_path)
        if result:
            print("✅ Migrazione completata con successo.")
        else:
            print("ℹ️ Nessun file migrato (già esistente o non trovato).")
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")

if __name__ == "__main__":
    main()
