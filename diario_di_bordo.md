# Diario di bordo Sistema Certificati. Aggiornamento riferito al 09/07/2025 (mattino) 

# Link al repo github: https://github.com/EmmeGasp/Revisione2 (mio branch refactoring-struttura)


## Stato attuale

- ** Creata struttura di base del progetto (src, data, logs, tests)
- ** Creato e attivato l'ambiente virtuale venv 
- ** Installate le dipendenze da requirements.txt
- ** Creato il branch rafactoring-struttura
- ** Spostati i file py esistenti nelle nuove directory
- ** Verificato la coerenza degli import con la nuova struttura file
- ** Modificato il percorso per accedere/salvare i file json per certificati e portafogli in base alla nuova struttura  
- ** Inserito il file main.py nel percorso di accesso
- ** Definito il contenuto del file main.py
- ** inserito il file vuoto --init.py-- nel percorso src per consentire il corretto avvio di main.py
- ** avviata la sistemazione del raccordo fra modalità di inserimento dei dati nella GUI con le esigenze di analisi che richedono una struttura di   certificati ben definta
- ** nuova gestione dei campi con miglioramento dell'inserimento mediante la clausola di 'opzionali', ferma la individuazione di quelli obbligatori
- ** migliorato l'inserimento e la visualizzazione dei valori numerici e percentuali
- ** i ticker dei titoli sottostanti sono lavorati nella fase di inserimento - GUI - per convertire i valori inseriti in lista, così come si aspetta la funzione che recupera i dati da yahoo. Allo stesso tempo viene salvaguardata la corretta visualizzazione dei ticker nel campo dedicato del dettaglio certificait.
- ** I campi vuoti nell'inserimento del certificato contengono 'None'; che però non assume rilevanza al fine del salvataggio dei dati, cioè viene evitato la conversione forzata a float di campi numerici non valorizzati perchè non obbligatori o, al momento dell'inserimento, non noti.
- ** in base all'applicazione del principio di delega, collocata nel file ehnanced_manager(...).py da main_window.py la routine che si occupa di recuperare i dati di mercato
- ** proseguita l'attività di raccordo fra i dati attesi dalle routine che dovranno occuparsi del recupero dei dati da yahoo con i dati acquisiti tramite GUI
- ** migliorate le annotazioni sul formato dei dati attesi in fase di inserimento. Ad esempio i numeri percentuali utilizzano come indicatore di decimali sempre il simbolo '.'. Per evitare conflitti fra il simbolo ',' come carattere separatore di liste e come separatore dei numeri decimali (diversi dalle percentuali, ad esempio prezzi di riferimento dei titoli sottostanti) è stato individuato il simbolo ';' quale separatore degli elenchi
- ** riscritte e aggiunte diversi metodi sempre in logica di raccordo fra le varie routine sempre in ottemperenza all'applicazione del principio di delega nonché di introduzione dei dati più semplice e di facile utilizzo (user friendly). Sono presenti annotazioni all'interno delle singole routine 
- ** Dopo le varie attività svolte è stata ripristinata e migliorata l'operatività CRUD, ivi incluso il calcolo delle date per le scadenze periodiche
- ** È operativo e funzionante il provider dati
- ** Testato il provider dati e raccordati i file affinchè il passaggio di dati avvenga come la procedura ricevente li desidera
- ** Diversi interventi su main_window.py e enhance_certificate_manager_fixed.py per miglorare la struttura di delega, il colloquio fra i file e sulla esposizione dei dati
- ** L'analisi dei dati viene ultimata. Adesso è necessario lavorare sulla qualità del dato estratto. Un primo intervento è stato effettuato sulla pulizia dei dati passati per il calcolo della volatilità omettendo i valori estremi
- ** Fra i dati esposti incluso anche il prezzo di mercato (ma attualmente la routine produce un errore da sistemare)



## Obiettivo corrente

  - ** Inserire la routine per la pulizia dei dati di mercato ai fini della determinazione della volatilità
  - ** Inserimento del prezzo di mercato del certificato oggetto di valutazione (fatto ma c'è un errore)
  - ** Aprire una finestra in luogo del box per esporre i risultati

## Passi completati. Note  

  ### Data di riferimento 03/07/2025 

- ** il refactor degli import è stato di fatto eseguito da Vscode che allo spostamento dei file si accorge della presenza di alcun import che richiedono un intervento. Ho solo verificato che non ci fossero più riferimenti 'old'. Ho lasciato invariato il file 'simple_gui_manager.py' in quanto sembra non impattare da questo punto di vista. Eventualmente il verificarsi di un errore smentirà questa affermazione.
- ** la scelta del dove traserire i file nella nuova struttura è ancora dozzinale; mi sono basato sul nome (gui --> ui, excel -->util) e guardando alcune delle funzioni svolte dal file. D'altra parte uno degli obiettivi è proprio quello di arrivare a spacchettare con logica funzionale i file py esistenti. Ho salvato il file 'Tabella raccordo File.xlsx' con l'elenco dei file trattati: dove erano e dove sono. Ho lasciato nel percorso base, quindi Revisione2, i file py che non fanno parte del progetto ma lavorano sul progetto (elenco classi/def per file, schema grafico di raccordo fra file).

  ### Data di riferimento 04/07/2025

- ** Dopo la esecuzione del refactoring ho rilanciato la routine inventory_class_functions.py che genera il report inventory_report.txt. Proprio per evidenziare meglio la evoluzione della struttura ho inserito a fianco del nome del file anche il percorso nel quale è collocato.
- ** Il programma viene eseguito e le principali attività (c.d. CURD) funzionano, sia per i certificati sia per i portafogli.  C'è da sistemare il file real_certificate_integration.py

  ### Data di riferimento 05/07/2025

- **Dopo le varie modifiche introdotte per migliorare il raccordo fra file, il sistema continua a funzionare ed anzi è migliorato in diversi aspetti.
  Ora il pulsnate che consente di Analizzare i certificati viene avviato ma si blocca a causa della mancanza dei dati di mercato, che rappresenta il prossimo obiettivo da raggiungere.

  ### Data di riferimento 08/07/2025
- ** Dopo l'attività di refactoring ed il riprisitino della operatività CRUD, deve essere avviata la fase di lavorazione dei dati di mercato  

  ### Data du riferimento 09/07/2025 (mattino, prima delle lavorazioni delle giornata)
- ** Inserita senza problemi la routine di pulizia dei dati
- ** Modificato main_window.py per recepire il prezzo di mercato. Generato errore da 'analysis_results' che risulta non definita
- ** I dati di mercato sono recuperati correttamente. È continuata l'attività di pulizia e raccordo. Ad esempio inserita routine per convertire le date delle scadenze da stringhe appunto a date, come si aspetta la routine che deve analizzare il rischio.  