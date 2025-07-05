# Diario di bordo Sistema Certificati. Aggiornamento riferito al 04/07/2025

# Link al repo github: https://github.com/EmmeGasp/Revisione2


## Stato attuale

- **Creata struttura di base del progetto (src, data, logs, tests)
- **Creato e attivato l'ambiente virtuale venv
- **Installato le dipendenze da requirements.txt; rispetto alla prima versione sono stte aggiunt3 altre 3 librerie
- **Creato il branch rafactoring-struttura
- ** Spostati i file py esistenti nelle nuove directory**
- ** Verificato la coerenza degli import con la nuova struttura file
- ** Modificato il percorso per accedere/salvare i file json per certificati e portafogli in base alla nuova struttura  
- ** Inserito il file main.py nel percorso di accesso
- ** Definito il contenuto del file main.py

## Obiettivo corrente

  - ** Sostituire il file real_certificate_integration.py con la nuova release che tiene conto dei nuovi campi introdotti
  - *(prima di fare questa sostituzione è necessario chiarire un dubbio in merito alla frase di chiusura contenuta nel nuovo file)
  - ** Spostare il file real_certificate_integration.py aggiornato da src\app\utils a src\app\core (attività sospesa in attesa di chiarimento)

## Passi completati. Note  

  ### Data di riferimento 03/07/2025 
- ** il refactor degli import è stato di fatto eseguito da Vscode che allo spostamento dei file si accorge della presenza di alcun import che richiedono un intervento. Ho solo verificato che non ci fossero più riferimenti 'old'. Ho lasciato invariato il file 'simple_gui_manager.py' in quanto sembra non impattare da questo punto di vista. Eventualmente il verificarsi di un errore smentirà questa affermazione.
- ** la scelta del dove traserire i file nella nuova struttura è ancora dozzinale; mi sono basato sul nome (gui --> ui, excel -->util) e guardando alcune delle funzioni svolte dal file. D'altra parte uno degli obiettivi è proprio quello di arrivare a spacchettare con logica funzionale i file py esistenti. Ho salvato il file 'Tabella raccordo File.xlsx' con l'elenco dei file trattati: dove erano e dove sono. Ho lasciato nel percorso base, quindi Revisione2, i file py che non fanno parte del progetto ma lavorano sul progetto (elenco classi/def per file, schema grafico di raccordo fra file).
  ### Data di riferimento 04/07/2025
- ** Dopo la esecuzione del refactoring ho rilanciato la routine inventory_class_functions.py che genera il report inventory_report.txt. Proprio per evidenziare meglio la evoluzione della struttura ho inserito a fianco del nome del file anche il percorso nel quale è collocato.
- ** Il programma viene eseguito e le principali attività (c.d. CURD) funzionano, sia per i certificati sia per i portafogli.  C'è da sistemare il file real_certificate_integration.py

 