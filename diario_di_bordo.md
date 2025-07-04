# Diario di bordo Sistema Certificati. Aggiornamento riferito al 3/7/2025


## Stato attuale

- **Creata struttura di base del progetto (src, data, logs, tests)
- **Creato e attivato l'ambiente virtuale venv
- **Installato le, per ora poche, dipendenze da requirements.txt
- **Creato il branch rafactoring-struttura
- ** Spostati i file py esistenti nelle nuove directory**
- ** Verificato la coerenza degli import con la nuova struttura file
- ** Modificato il percorso per accedere/salvare i file json per certificati e portafogli  in base alla nuova struttura  
- ** Inserito il file main.py nel percorso di accesso

## Obiettivo corrente

  - **Verificare se è possibile avviare il sistema dopo gli interventi descritti

## Passi completati. Note  
 
- ** il refactor degli import è stato di fatto eseguito da Vscode che allo spostamento dei file si accorge della presenza di alcun import che richiedono un intervento. Ho solo verificato che non ci fossero più riferimenti 'old'. Ho lasciato invariato il file 'simple_gui_manager.py' in quanto sembra non impattare da questo punto di vista. Eventualmente il verificarsi di un errore smentirà questa affermazione.
- ** la scelta del dove traserire i file nella nuova struttura è ancora dozzinale; mi sono basato sul nome (gui --> ui, excel -->util) e guardando alcune delle funzioni svolte dal file. D'altra parte uno degli obiettivi è proprio quello di arrivare a spacchettare con logica funzionale i file py esistenti. Ho salvato il file 'Tabella raccordo File.xlsx' con l'elenco dei file trattati: dove erano e dove sono. Ho lasciato nel percorso base, quindi Revisione2, i file py che non fanno parte del progetto ma lavorano sul progetto (elenco classi/def per file, schema grafico di raccordo fra file).
 