# Diario Debug Airbag - Certificati v15.1

## Situazione attuale (fine giornata)

- **Problema:** Il campo "Livello Airbag (%)" nella maschera di modifica non viene mai popolato, anche se il valore è presente nel file JSON e viene visualizzato correttamente nella finestra dettaglio.
- **Test effettuati:**  
  - Inserimento e salvataggio di vari valori (es. 50, 65, 35.5) → sempre non visibile in modifica.
  - Il campo note airbag si comporta allo stesso modo: il valore non viene mai riproposto in modifica.
  - Il file JSON viene aggiornato correttamente con i valori inseriti.
  - La finestra dettaglio mostra sempre il valore corretto.
- **Ultime modifiche:**  
  - Caricamento dei campi airbag_feature, airbag_level, airbag_notes in ordine, con conversione e salvataggio forzato anche di stringhe vuote.
  - Nessun errore di runtime, nessun crash.
- **Risultato:**  
  - Nessun cambiamento nel comportamento: i valori non vengono mai riproposti in modifica.

## Prossimi passi (per la nuova chat/debug di domani)

- Eseguire la routine di modifica in modalità debug, con breakpoint su:
  - `_load_existing_data_v15_1_corrected` (verificare che il valore venga effettivamente letto e inserito nel campo Entry/Text).
  - `_toggle_airbag_level_field` (verificare che non venga cancellato subito dopo).
  - Eventuali altri metodi che possono interferire con la visualizzazione dei campi.
- Verificare se ci sono errori silenziosi o reset dei widget dopo il caricamento.
- Annotare eventuali differenze tra il valore letto dal file e quello effettivamente visualizzato nel campo Entry/Text.
- Valutare se la logica di abilitazione/disabilitazione dei campi interferisce con la visualizzazione.

## Note

- Il problema non riguarda la serializzazione/salvataggio, ma solo la visualizzazione in modifica.
- Il campo viene sempre letto dal file e passato correttamente alla funzione di caricamento.
- Il valore viene sempre mostrato nella finestra dettaglio, quindi è presente nel dict.
- Il problema sembra legato solo alla GUI (Tkinter Entry/Text) e alla sequenza di chiamate/metodi.

---

**Pronto per debug step-by-step domani.**
