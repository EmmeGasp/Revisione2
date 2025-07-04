# Diario Chat - Sistema Certificati v15.1

## Ultimi aggiornamenti e punti aperti

- **Inserimento manuale certificati**: Testato con successo l’inserimento di diversi certificati reali, anche con casi particolari.
- **Campi aggiuntivi**: Integrati i campi per prezzi iniziali/strike dei sottostanti e note barriere (da completare la visualizzazione/gestione se necessario).
- **Emittenti**: Aggiunti Unicredit e Intesa Sanpaolo tra gli emittenti selezionabili.
- **Tipologia certificato**: Aggiunta la voce "digitale" e nota ACEPI accanto al campo tipo.
- **Formato prezzi**: Indicazione chiara del formato accanto al campo prezzi iniziali/strike.
- **Visualizzazione prezzi**: I prezzi vengono visualizzati con separatore migliaia e decimali in modo leggibile.
- **Gestione tipologie di portafoglio**:  
  - **TODO**: Implementare la gestione completa delle tipologie di portafoglio (inserisci, modifica, elimina) tramite apposita interfaccia. Attualmente la scelta è possibile solo tra quelle predefinite; la gestione dinamica sarà sviluppata in seguito.
- **TODO**: 
  - Verificare che il campo "Note Barriere" sia sempre presente e ben visibile sia in inserimento che in visualizzazione dettagli (attualmente da ricontrollare la posizione e la gestione).
  - Migliorare la gestione di casi particolari di barriere variabili/complesse.
  - **Prossimo passo: analisi dei certificati** (approfondire la funzionalità di analisi, visualizzazione avanzata e reportistica dei singoli certificati).
- **Nota**: Serve davvero una gestione robusta dei campi opzionali e non previsti nei costruttori delle classi (es. titoli sottostanti, certificato, altri parametri): è necessario filtrare sempre i parametri in eccesso prima di creare oggetti, per evitare errori di tipo "unexpected keyword argument".

---

**Nota**: Se necessario, tornare a migliorare la UX sulla pulizia automatica dei campi airbag e completare la gestione delle note barriere.
