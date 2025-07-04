# -*- coding: utf-8 -*-

"""
Punto di ingresso principale per l'applicazione di analisi dei certificati finanziari.

Questo script ha la sola responsabilità di:
1. Importare la classe principale dell'interfaccia utente (GUI).
2. Creare un'istanza dell'applicazione.
3. Avviare l'applicazione.

Per eseguire l'applicazione dalla directory radice del progetto (contenente 'src', 'venv', etc.),
usare il comando:
python src/main.py
"""

import sys
import os

# --- Blocco per la gestione dei percorsi ---
# Questo blocco assicura che il pacchetto 'app' possa essere importato correttamente
# quando lo script viene eseguito, aggiungendo la directory 'src' al path di Python.
# È una pratica robusta per garantire che gli import funzionino indipendentemente
# da come e da dove viene lanciato lo script.
try:
    # Aggiunge la directory 'src' al path di sistema per trovare il pacchetto 'app'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # Importa la classe principale dell'interfaccia utente dal file corretto.
    # Il nome della classe è stato identificato dal file main_window.py fornito.
    from app.ui.main_window import SimpleCertificateGUIManagerV15_1_Corrected

except ImportError as e:
    # Se l'import fallisce, mostra un messaggio di errore chiaro ed esci.
    # Questo aiuta a diagnosticare rapidamente problemi di struttura o di nomi di file/classi.
    print("--- ERRORE CRITICO DI IMPORTAZIONE ---")
    print(f"Impossibile avviare l'applicazione a causa di un ImportError: {e}")
    print("\nPossibili cause:")
    print("1. Il file 'src/app/ui/main_window.py' non è stato trovato o rinominato.")
    print("2. La classe 'SimpleCertificateGUIManagerV15_1_Corrected' non esiste in tale file.")
    print("3. La struttura delle directory non corrisponde a quella prevista ('src/app/ui/...')")
    print(f"4. Il percorso di sistema Python attuale è: {sys.path}")
    sys.exit(1) # Esce dal programma con un codice di errore.


def start_application():
    """
    Inizializza e avvia l'applicazione GUI.
    """
    try:
        # Crea un'istanza della classe principale dell'applicazione.
        # Questa classe gestisce internamente la creazione della finestra radice di Tkinter.
        app = SimpleCertificateGUIManagerV15_1_Corrected()

        # Chiama il metodo run() dell'applicazione per avviare il ciclo di eventi
        # e mostrare la finestra.
        app.run()

    except Exception as e:
        # Cattura qualsiasi altra eccezione imprevista durante l'avvio
        # per fornire un feedback utile.
        print(f"Si è verificato un errore imprevisto durante l'avvio dell'applicazione: {e}")
        # In un'applicazione reale, qui si potrebbe scrivere l'errore in un file di log.
        import traceback
        traceback.print_exc()
        sys.exit(1)


# --- Blocco di esecuzione principale ---
# Il costrutto 'if __name__ == "__main__"' è una convenzione standard in Python.
# Assicura che la funzione start_application() venga chiamata solo quando
# questo file viene eseguito direttamente, e non quando viene importato da un altro script.
if __name__ == "__main__":
    print("Avvio dell'applicazione Certificati Finanziari...")
    start_application()
    print("Applicazione terminata.")
