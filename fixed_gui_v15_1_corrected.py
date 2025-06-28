# ==========================================================
# NOME FILE: fixed_gui_v15_1_corrected.py
# SCOPO: Gestione GUI avanzata per inserimento, modifica e visualizzazione certificati finanziari v15.1
# AUTORE: Team di sviluppo
# DATA CREAZIONE: 2024-06-22
# ULTIMA MODIFICA: 2024-06-22
# VERSIONE: 1.0
# ==========================================================
#
# DESCRIZIONE:
# Modulo principale per la gestione grafica (Tkinter) dei certificati finanziari.
# Permette inserimento, modifica, validazione e visualizzazione dettagliata dei certificati,
# con supporto a tutti i nuovi campi v15.1, gestione barriere dinamiche, note, e integrazione
# con sistemi di calcolo date e portfolio manager.
#
# PRINCIPALI CLASSI/FUNZIONI:
# - EnhancedCertificateDialogV15_1_Corrected: Dialog avanzato per inserimento/modifica certificato
# - SimpleCertificateGUIManagerV15_1_Corrected: Gestione GUI principale e interazione utente
#
# DIPENDENZE:
# - tkinter, json, pathlib, moduli interni (real_certificate_integration, enhanced_certificate_manager_fixed, ecc.)
#
# NOTE:
# - Il file include fix per compatibilità RealCertificateConfig e gestione risk-free rate.
# - La struttura è pronta per estensioni future e integrazione con portfolio manager.
# ==========================================================

# ==========================================================
# RIEPILOGO CONTENUTO FILE:
# - Classi GUI: EnhancedCertificateDialogV15_1_Corrected
# - Import e compatibilità con RealCertificateConfig, EnhancedCertificateManagerV15
# - Gestione completa campi certificato, conversione, validazione, dialog avanzato
# ==========================================================

# ========================================
# Fixed GUI Manager v15.1 CORRECTED - Versione Funzionante
# Timestamp: 2025-06-21 18:00:00 (Aggiornato)
# Fix: Compatibilità v15.1 con RealCertificateConfig
# ========================================

"""
*** SISTEMA CERTIFICATI v15.1 CORRECTED - VERSIONE FUNZIONANTE ***

CORREZIONI v15.1 CORRECTED:
✅ FIX CRITICO: Compatibilità campi v15.1 con RealCertificateConfig
✅ Conversione automatica: coupon_barrier_type -> barrier_levels['coupon']
✅ Tutti i campi nuovi supportati senza errori
✅ Backward compatibility completa
✅ Sistema stabile e pronto per produzione
✅ Larghezza campo descrizione sottostanti aumentata
✅ Descrizione dinamica per Tipo Dipendenza Sottostanti
✅ Frequenza "Quadrimestrale" aggiunta
✅ Dettagli certificato aggiornati con nuovi campi e precisione
✅ Gestione Barriera Dinamica integrata nel tipo barriera capitale
✅ Precisione a 3 decimali per Tasso Cedola
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import threading
import calendar 
import copy
import textwrap # Per formattare la descrizione della dipendenza

# Import sistema esistente
try:
    from real_certificate_integration import (
        RealCertificateConfig, IntegratedCertificateSystem
    )
    print("✅ Import sistema esistente OK")
    
    # Import enhanced manager per calc date
    try:
        from enhanced_certificate_manager_fixed import (
            EnhancedCertificateManagerV15, 
            CalculoDateAutoDialogV15,
            DateCalculationUtils
        )
        print("✅ Import enhanced manager v15 OK")
        ENHANCED_MANAGER_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ Enhanced manager non disponibile: {e}")
        ENHANCED_MANAGER_AVAILABLE = False

except ImportError as e:
    print(f"⚠️ Import sistema: {e}")
    # Dummy classes per evitare errori
    class RealCertificateConfig:
        pass
    class IntegratedCertificateSystem:
        pass
    ENHANCED_MANAGER_AVAILABLE = False

# ========================================
# ENHANCED CERTIFICATE DIALOG v15.1 CORRECTED - FORM COMPLETO
# ========================================

class EnhancedCertificateDialogV15_1_Corrected:
    """Dialog certificato completo v15.1 CORRECTED con TUTTI i campi necessari"""
    
    # Mappa descrizioni per Tipo Dipendenza - DEFINITO COME ATTRIBUTO DI CLASSE
    _dependency_descriptions = {
        'Worst-Of': "🔻 WORST-OF: Il peggiore tra tutti determina il payoff (MASSIMO RISCHIO). Performance = MIN(asset1, asset2, asset3, ...) - Basta che uno crolli!",
        'Best-Of': "🔺 BEST-OF: Il migliore tra tutti determina il payoff (MINIMO RISCHIO). Performance = MAX(asset1, asset2, asset3, ...) - Uno solo deve andare bene.",
        'Average': "📈 AVERAGE/BASKET: Performance media ponderata (RISCHIO INTERMEDIO). Performance = MEDIA(asset1, asset2, asset3, ...) - Compensazione reciproca.",
        'Single': "🌈 RAINBOW/INDIVIDUAL: Ogni asset contribuisce individualmente. Payoff calcolato per singolo sottostante - Struttura complessa.", # Mappato a Rainbow
        'Basket Custom': "🌈 RAINBOW/INDIVIDUAL: Ogni asset contribuisce individualmente. Payoff calcolato per singolo sottostanti - Struttura complessa." # Mappato a Rainbow
    }

    def __init__(self, parent, title, existing_data=None):
        self.result = None
        self.existing_data = copy.deepcopy(existing_data) if existing_data else {}
        self.dialog_closed = False
        
        print(f"📝 === APERTURA DIALOG v15.1 CORRECTED ===")
        print(f"📝 Title: {title}")
        if existing_data:
            print(f"📝 Dati esistenti: {list(existing_data.keys())}")
            print(f"📝 Risk-Free Rate esistente: {existing_data.get('risk_free_rate', 'N/A')}")
        else:
            print(f"📝 Nuovo certificato (form vuoto)")
        
        # Finestra ottimizzata
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title + " - v15.1 CORRECTED")
        self.dialog.geometry("1000x900")  # Più spazio per tutti i campi
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Gestione chiusura
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_dialog_close)
        
        # Centra dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500)
        y = (self.dialog.winfo_screenheight() // 2) - (450)
        self.dialog.geometry(f"1000x900+{x}+{y}")
        
        # Setup form completo
        self._setup_form_complete_v15_1_corrected()
        
        # Attesa
        self.dialog.wait_window()
    
    def _on_dialog_close(self):
        """Gestione chiusura dialog"""
        print("❌ Dialog v15.1 CORRECTED chiuso senza salvare")
        self.result = None
        self.dialog_closed = True
        self.dialog.destroy()
    
    def _setup_form_complete_v15_1_corrected(self):
        """Setup form completo v15.1 CORRECTED con TUTTI i campi"""
        
        # Main container
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollable area
        canvas = tk.Canvas(main_container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(main_container, orient="horizontal", command=canvas.xview)
        
        # Frame scrollable
        self.scrollable_frame = ttk.Frame(canvas)
        
        # Configurazione scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Fixed bottom frame - Pulsanti sempre visibili
        fixed_bottom_frame = ttk.Frame(main_container)
        fixed_bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Separatore
        ttk.Separator(fixed_bottom_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
        
        # Pulsanti fissi
        button_frame = ttk.Frame(fixed_bottom_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="❌ Annulla", 
                  command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="💾 Salva Certificato v15.1", 
                  command=self._save_v15_1_corrected).pack(side=tk.RIGHT)
        
        # Scroll area
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Window nel canvas
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Bind per ridimensionamento
        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Mouse wheel scroll
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Crea form fields COMPLETO
        self._create_complete_form_fields_v15_1_corrected()
    
    def _create_complete_form_fields_v15_1_corrected(self):
        """*** FORM COMPLETO v15.1 CORRECTED *** - TUTTI i campi necessari"""
        
        self.fields = {}
        
        print("🏗️ === CREAZIONE FORM COMPLETO v15.1 CORRECTED ===")
        
        # =======================================
        # SEZIONE 1: INFORMAZIONI BASE
        # =======================================
        
        base_frame = ttk.LabelFrame(self.scrollable_frame, text="📋 Informazioni Base", padding=15)
        base_frame.pack(fill='x', padx=10, pady=5)
        
        # Row 1: ISIN e Nome
        row1_frame = ttk.Frame(base_frame)
        row1_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1_frame, text="ISIN:", width=15).pack(side=tk.LEFT)
        self.fields['isin'] = ttk.Entry(row1_frame, width=20, font=('Arial', 10, 'bold'))
        self.fields['isin'].pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1_frame, text="Nome:", width=15).pack(side=tk.LEFT)
        self.fields['name'] = ttk.Entry(row1_frame, width=30)
        self.fields['name'].pack(side=tk.LEFT, padx=(5, 0))
        
        # NUOVO: Ticker Strumento Certificato (Opzionale)
        ttk.Label(row1_frame, text="Ticker Strumento:", width=15).pack(side=tk.LEFT, padx=(20,0)) # Spazio aggiunto
        self.fields['certificate_instrument_ticker'] = ttk.Entry(row1_frame, width=15)
        self.fields['certificate_instrument_ticker'].pack(side=tk.LEFT, padx=(5,0))
        
        # Row 2: Emittente e Tipo
        row2_frame = ttk.Frame(base_frame)
        row2_frame.pack(fill=tk.X, pady=5)

        ttk.Label(row2_frame, text="Emittente:", width=15).pack(side=tk.LEFT)
        self.fields['issuer'] = ttk.Combobox(
            row2_frame, width=18,
            values=[
                'Vontobel', 'BNP Paribas', 'Société Générale',
                'Goldman Sachs', 'Morgan Stanley', 'Unicredit', 'Intesa Sanpaolo', 'Altro'
            ]
        )
        self.fields['issuer'].pack(side=tk.LEFT, padx=(5, 20))

        # *** NUOVO v15.1 *** - Campo Tipo Certificato
        ttk.Label(row2_frame, text="Tipo:", width=15).pack(side=tk.LEFT)
        self.fields['certificate_type'] = ttk.Combobox(
            row2_frame, width=18,
            values=[
                'express', 'cash_collect', 'phoenix', 'barrier_reverse_convertible', 'digitale'
            ]
        )
        self.fields['certificate_type'].pack(side=tk.LEFT, padx=(5, 0))
        # Nota ACEPI accanto al tipo certificato
        ttk.Label(
            row2_frame,
            text="(Usa classificazione ACEPI se possibile)",
            font=('Arial', 8, 'italic'),
            foreground='gray'
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Row 3: Date
        row3_frame = ttk.Frame(base_frame)
        row3_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(row3_frame, text="Data Emissione:", width=15).pack(side=tk.LEFT)
        self.fields['issue_date'] = ttk.Entry(row3_frame, width=12)
        self.fields['issue_date'].pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row3_frame, text="Scadenza:", width=15).pack(side=tk.LEFT)
        self.fields['maturity_date'] = ttk.Entry(row3_frame, width=12)
        self.fields['maturity_date'].pack(side=tk.LEFT, padx=(5, 0))

        
        
        # =======================================
        # SEZIONE 2: PARAMETRI FINANZIARI - FIX RISK-FREE RATE
        # =======================================
        
        financial_frame = ttk.LabelFrame(self.scrollable_frame, text="💰 Parametri Finanziari", padding=15)
        financial_frame.pack(fill='x', padx=10, pady=5)
        
        # Row 1: Nominale e Risk-Free Rate FIX
        fin_row1_frame = ttk.Frame(financial_frame)
        fin_row1_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(fin_row1_frame, text="Nominale:", width=15).pack(side=tk.LEFT)
        self.fields['notional'] = ttk.Entry(fin_row1_frame, width=15)
        self.fields['notional'].pack(side=tk.LEFT, padx=(5, 20))
        
        # *** FIX RISK-FREE RATE v15.1 *** - Formato unificato percentuale
        ttk.Label(fin_row1_frame, text="Risk-Free Rate (%):", width=18).pack(side=tk.LEFT)
        self.fields['risk_free_rate'] = ttk.Entry(fin_row1_frame, width=10)
        self.fields['risk_free_rate'].pack(side=tk.LEFT, padx=(5, 5))
    
        # Label informativo per formato
        ttk.Label(fin_row1_frame, text="(es: 3.5 per 3.5%, usa '.' come decimale)", 
                 font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(5, 0))
        
        # *** NUOVO v15.1 *** - Tasso Cedola
        fin_row2_frame = ttk.Frame(financial_frame)
        fin_row2_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(fin_row2_frame, text="Tasso Cedola (% del periodo):", width=25).pack(side=tk.LEFT) # Label modificata
        self.fields['coupon_rate'] = ttk.Entry(fin_row2_frame, width=10)
        self.fields['coupon_rate'].pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(fin_row2_frame, text="Frequenza:", width=15).pack(side=tk.LEFT)
        self.fields['coupon_frequency'] = ttk.Combobox(fin_row2_frame, width=12, state='readonly',
                                                     values=['Mensile', 'Bimestrale', 'Trimestrale', 'Quadrimestrale', 'Semestrale', 'Annuale'])
        self.fields['coupon_frequency'].pack(side=tk.LEFT, padx=(5, 0))

        # Valuta Certificato (Spostata qui)
        ttk.Label(fin_row2_frame, text="Valuta Certificato:", width=18).pack(side=tk.LEFT, padx=(20,0)) # Spazio aggiunto
        self.fields['currency'] = ttk.Combobox(fin_row2_frame, width=8, state='readonly',
                                             values=['EUR', 'USD', 'GBP', 'CHF', 'JPY'])
        self.fields['currency'].pack(side=tk.LEFT, padx=(5, 0))
        
        # =======================================
        # SEZIONE 3: CARATTERISTICHE PRODOTTO - MEMORIA E AIRBAG
        # =======================================
        
        features_frame = ttk.LabelFrame(self.scrollable_frame, text="🛡️ Caratteristiche Prodotto", padding=15)
        features_frame.pack(fill='x', padx=10, pady=5)
        
        # Memory Feature
        memory_frame = ttk.Frame(features_frame)
        memory_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(memory_frame, text="Effetto Memoria:", width=15).pack(side=tk.LEFT)
        self.fields['memory_feature'] = ttk.Combobox(memory_frame, width=12,
                                                   values=['True', 'False'])
        self.fields['memory_feature'].pack(side=tk.LEFT, padx=(5, 20))

        # Airbag Feature e Livello Airbag (nello stesso frame per allineamento)
        airbag_control_frame = ttk.Frame(features_frame)
        airbag_control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(airbag_control_frame, text="Airbag:", width=15).pack(side=tk.LEFT)
        self.fields['airbag_feature'] = ttk.Combobox(airbag_control_frame, width=12,
                                                   values=['True', 'False'])
        self.fields['airbag_feature'].pack(side=tk.LEFT, padx=(5, 20))
        # Usa il bind con clear_on_disable=True SOLO per l'interazione utente
        self.fields['airbag_feature'].bind(
            "<<ComboboxSelected>>",
            lambda event: self._toggle_airbag_level_field(event, clear_on_disable=True)
        )

        self.airbag_level_label = ttk.Label(airbag_control_frame, text="Livello Airbag (%):", width=15)
        self.airbag_level_label.pack(side=tk.LEFT)
        self.fields['airbag_level'] = ttk.Entry(airbag_control_frame, width=10)
        self.fields['airbag_level'].pack(side=tk.LEFT, padx=(5, 0))

        # --- Campo note airbag ---
        self.airbag_notes_label = ttk.Label(airbag_control_frame, text="Note Airbag:", width=12)
        self.airbag_notes_label.pack(side=tk.LEFT, padx=(20, 0))
        self.fields['airbag_notes'] = tk.Text(airbag_control_frame, width=30, height=2, wrap=tk.WORD)
        self.fields['airbag_notes'].pack(side=tk.LEFT, padx=(5, 0))
        # --- Fine campo note airbag ---

        # Inizializza lo stato del campo Livello Airbag
        self._toggle_airbag_level_field()

        
        # =======================================
        # SEZIONE 4: BARRIERE
        # =======================================
        
        barriers_frame = ttk.LabelFrame(self.scrollable_frame, text="🚧 Livelli Barriera", padding=15)
        barriers_frame.pack(fill='x', padx=10, pady=5)
        
        # Barriera Cedola
        barrier_row1_frame = ttk.Frame(barriers_frame)
        barrier_row1_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(barrier_row1_frame, text="Barriera Cedola (%):", width=18).pack(side=tk.LEFT)
        self.fields['coupon_barrier'] = ttk.Entry(barrier_row1_frame, width=10)
        self.fields['coupon_barrier'].pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(barrier_row1_frame, text="Tipo:", width=8).pack(side=tk.LEFT)
        self.fields['coupon_barrier_type'] = ttk.Combobox(barrier_row1_frame, width=12, state='readonly',
                                                        values=['none', 'european', 'american'])
        self.fields['coupon_barrier_type'].pack(side=tk.LEFT, padx=(5, 0))
        
        # Barriera Capitale
        barrier_row2_frame = ttk.Frame(barriers_frame)
        barrier_row2_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(barrier_row2_frame, text="Barriera Capitale (%):", width=18).pack(side=tk.LEFT)
        self.fields['capital_barrier'] = ttk.Entry(barrier_row2_frame, width=10)
        self.fields['capital_barrier'].pack(side=tk.LEFT, padx=(5, 20))
        

        ttk.Label(barrier_row2_frame, text="Tipo:", width=8).pack(side=tk.LEFT)
        self.fields['capital_barrier_type'] = ttk.Combobox(barrier_row2_frame, width=12, state='readonly',
                                                         values=['protected', 'none', 'dynamic']) # Rimosso 'airbag'        
        self.fields['capital_barrier_type'].pack(side=tk.LEFT, padx=(5, 0))
        self.fields['capital_barrier_type'].bind("<<ComboboxSelected>>", self._on_capital_barrier_type_changed) # Bind nuovo metodo
    
        # --- NUOVA SEZIONE: Parametri Barriera Dinamica (inizialmente nascosta) ---
        # self.dynamic_barrier_params_frame = ttk.LabelFrame(self.scrollable_frame, text="⚙️ Parametri Barriera Dinamica", padding=15)
        # --- NUOVA SEZIONE: Parametri Barriera Dinamica (inizialmente nascosta, ora dentro barriers_frame) ---
        self.dynamic_barrier_params_frame = ttk.LabelFrame(barriers_frame, text="⚙️ Parametri Barriera Dinamica", padding=15)
        # Non packare qui, sarà gestito da _on_capital_barrier_type_changed

        # Livello Iniziale (dynamic_barrier_start_level) -- *** AGGIUNTO ***
        db_row1_frame = ttk.Frame(self.dynamic_barrier_params_frame)
        db_row1_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_row1_frame, text="Livello Iniziale (%):", width=25).pack(side=tk.LEFT)
        self.fields['dynamic_barrier_start_level'] = ttk.Entry(db_row1_frame, width=10)
        self.fields['dynamic_barrier_start_level'].pack(side=tk.LEFT, padx=(5, 20))

        # Step Down Rate
        db_row2_frame = ttk.Frame(self.dynamic_barrier_params_frame)
        db_row2_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_row2_frame, text="Step Down Rate (%):", width=25).pack(side=tk.LEFT)
        self.fields['step_down_rate'] = ttk.Entry(db_row2_frame, width=10)
        self.fields['step_down_rate'].pack(side=tk.LEFT, padx=(5, 20))

        # Livello Finale
        db_row3_frame = ttk.Frame(self.dynamic_barrier_params_frame)
        db_row3_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_row3_frame, text="Livello Finale (%):", width=25).pack(side=tk.LEFT)
        self.fields['dynamic_barrier_end_level'] = ttk.Entry(db_row3_frame, width=10)
        self.fields['dynamic_barrier_end_level'].pack(side=tk.LEFT, padx=(5, 0))

        # Mesi di Ritardo Osservazione (nuovo campo)
        db_row4_frame = ttk.Frame(self.dynamic_barrier_params_frame)
        db_row4_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_row4_frame, text="Mesi di Ritardo Osservazione:", width=25).pack(side=tk.LEFT)
        self.fields['observation_delay_months'] = ttk.Entry(db_row4_frame, width=10)
        self.fields['observation_delay_months'].pack(side=tk.LEFT, padx=(5, 0))
        # --- Fine NUOVA SEZIONE ---

        # --- CAMPO NOTE BARRIERE ---
        note_barriere_frame = ttk.Frame(barriers_frame)
        note_barriere_frame.pack(fill=tk.X, pady=5)
        ttk.Label(note_barriere_frame, text="Note Barriere:", width=15).pack(side=tk.LEFT)
        self.fields['note_barriere'] = tk.Text(note_barriere_frame, width=60, height=2, wrap=tk.WORD)
        self.fields['note_barriere'].pack(side=tk.LEFT, padx=(5, 0))
        # --- FINE CAMPO NOTE BARRIERE ---

        # =======================================
        # SEZIONE 5: SOTTOSTANTI
        # =======================================
        
        underlying_frame = ttk.LabelFrame(self.scrollable_frame, text="📈 Sottostanti", padding=15)
        underlying_frame.pack(fill='x', padx=10, pady=5)
        
        # Tickers Yahoo Sottostanti
        ticker_frame = ttk.Frame(underlying_frame)
        ticker_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ticker_frame, text="Tickers Sottostanti (Yahoo, virgola sep.):", width=35).pack(side=tk.LEFT)
        self.fields['yahoo_ticker'] = ttk.Entry(ticker_frame, width=40)
        self.fields['yahoo_ticker'].pack(side=tk.LEFT, padx=(5, 20))

        # Prezzi iniziali/strike/prezzi di riferimento
        strike_frame = ttk.Frame(underlying_frame)
        strike_frame.pack(fill=tk.X, pady=5)
        ttk.Label(strike_frame, text="Prezzi Iniziali/Strike (virgola sep.):", width=35).pack(side=tk.LEFT)
        self.fields['prezzi_iniziali_sottostanti'] = ttk.Entry(strike_frame, width=40)
        self.fields['prezzi_iniziali_sottostanti'].pack(side=tk.LEFT, padx=(5, 5))
        # Indicazione formato inserimento
        ttk.Label(
            strike_frame,
            text="(es: 1.234,56 oppure 1234.56 - usa ',' per decimali, '.' per migliaia)",
            font=('Arial', 8), foreground='gray'
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Nomi/Descrizioni Sottostanti
        desc_frame = ttk.Frame(underlying_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="Nomi/Desc Sottostanti (virgola sep.):", width=35).pack(side=tk.LEFT)
        self.fields['underlying_names'] = ttk.Entry(desc_frame, width=60) # Larghezza aumentata
        self.fields['underlying_names'].pack(side=tk.LEFT, padx=(5,0))
        
        # Valute Sottostanti
        currency_frame = ttk.Frame(underlying_frame) # Nuovo frame per le valute
        currency_frame.pack(fill=tk.X, pady=5)

        ttk.Label(currency_frame, text="Valute Sottostanti (virgola sep.):", width=35).pack(side=tk.LEFT)
        self.fields['underlying_currencies'] = ttk.Entry(currency_frame, width=40) # Nuovo campo per valute sottostanti
        self.fields['underlying_currencies'].pack(side=tk.LEFT, padx=(5, 20))

        # Tipo Dipendenza Sottostanti (Worst-of, etc.)
        dependency_frame = ttk.Frame(underlying_frame)
        dependency_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dependency_frame, text="Tipo Dipendenza Sottostanti:", width=35).pack(side=tk.LEFT)
        self.fields['underlying_dependency_type'] = ttk.Combobox(dependency_frame, width=25, state='readonly', # Larghezza aumentata
                                                               values=['Worst-Of', 'Best-Of', 'Average', 'Single', 'Basket Custom'])
        self.fields['underlying_dependency_type'].pack(side=tk.LEFT, padx=(5,0))
        self.fields['underlying_dependency_type'].bind("<<ComboboxSelected>>", self._update_dependency_description)

        # Descrizione Tipo Dipendenza (Label)
        self.dependency_description_label = ttk.Label(underlying_frame, text="", 
                                                     font=("Arial", 9, "italic"), 
                                                     foreground="gray", 
                                                     wraplength=700) # A capo automatico
        self.dependency_description_label.pack(fill=tk.X, padx=10, pady=(0, 5))
        # Aggiorna descrizione iniziale
        self._update_dependency_description()    

        # =======================================
        # CARICA DATI ESISTENTI v15.1
        # =======================================
        
        self._load_existing_data_v15_1_corrected()
        
        # Focus su primo campo
        self.fields['isin'].focus()
        
        print("✅ Form completo v15.1 CORRECTED creato con successo")
    
    def _load_existing_data_v15_1_corrected(self):
        """*** CARICAMENTO DATI v15.1 CORRECTED *** - Con fix Risk-Free Rate"""
        
        if not self.existing_data:
            # Valori default per nuovo certificato
            self.fields['issuer'].set('Vontobel')
            self.fields['certificate_type'].set('express')
            self.fields['issue_date'].insert(0, '2024-01-15')
            self.fields['maturity_date'].insert(0, '2027-01-15')
            self.fields['notional'].insert(0, '1000')
            self.fields['risk_free_rate'].insert(0, '3.50')  # Formato percentuale, 2 decimali
            self.fields['coupon_rate'].insert(0, '2.500') # 3 decimali per 0.667%
            self.fields['coupon_frequency'].set('Trimestrale')
            self.fields['memory_feature'].set('False')
            self.fields['airbag_feature'].set('False')
            self.fields['coupon_barrier_type'].set('none')
            self.fields['capital_barrier_type'].set('protected')
            self.fields['currency'].set('EUR')
            # Default values for dynamic barrier fields (will be hidden initially)
            self.fields['dynamic_barrier_start_level'].insert(0, '100.00')
            self.fields['dynamic_barrier_end_level'].insert(0, '73.00')
            self.fields['underlying_dependency_type'].set('Worst-Of') # Default per dipendenza
            self.fields['certificate_instrument_ticker'].insert(0, '') # Default vuoto
            self.fields['underlying_names'].insert(0, '') # Default vuoto
            self.fields['underlying_currencies'].insert(0, '') # Default vuoto
            print("✅ Valori default caricati per nuovo certificato")
            return
        
        print("📊 === CARICAMENTO DATI ESISTENTI v15.1 CORRECTED ===")
        
        # *** FIX RISK-FREE RATE v15.1 *** - Conversione formato
        risk_free_rate = self.existing_data.get('risk_free_rate', 0.035)
        print(f"📊 Risk-Free Rate originale: {risk_free_rate} (tipo: {type(risk_free_rate)})")
        
        # Conversione intelligente a percentuale
        if isinstance(risk_free_rate, (int, float)):
            if risk_free_rate <= 1.0:  # Formato decimale (es: 0.035)
                risk_free_percentage = risk_free_rate * 100  # Converti a 3.5
            else:  # Già in percentuale (es: 3.5)
                risk_free_percentage = risk_free_rate
        else:
            try:
                rf_float = float(str(risk_free_rate))
                risk_free_percentage = rf_float * 100 if rf_float <= 1.0 else rf_float
            except:
                risk_free_percentage = 3.50  # Default
        
        print(f"📊 Risk-Free Rate convertito: {risk_free_percentage}% (display)")
        
        # Carica da dati esistenti con mapping completo
        field_mapping = {
            'isin': 'isin',
            'name': 'name', 
            'issuer': 'issuer',
            'certificate_type': 'certificate_type',
            'issue_date': 'issue_date',
            'maturity_date': 'maturity_date',
            'notional': 'notional',
            'coupon_rate': 'coupon_rate',
            'coupon_frequency': 'coupon_frequency',
            'memory_feature': 'memory_feature',
            'airbag_feature': 'airbag_feature',
            'airbag_level': 'airbag_level',
            'airbag_notes': 'airbag_notes',
            'coupon_barrier': 'coupon_barrier',
            'coupon_barrier_type': 'coupon_barrier_type',
            'capital_barrier': 'capital_barrier',
            'capital_barrier_type': 'capital_barrier_type',
            'certificate_instrument_ticker': 'certificate_instrument_ticker', # Nuovo
            'underlying_currencies': 'underlying_currencies', # Aggiunto per caricamento
            'underlying_names': 'underlying_names', # Nuovo
            'underlying_dependency_type': 'underlying_dependency_type', # Nuovo
            'yahoo_ticker': 'yahoo_ticker',
            'currency': 'currency',
            'dynamic_barrier_start_level': 'dynamic_barrier_start_level', # Nuovo
            'step_down_rate': 'step_down_rate', # Nuovo
            'dynamic_barrier_end_level': 'dynamic_barrier_end_level', # Nuovo
            'observation_delay_months': 'observation_delay_months', # Nuovo
            'prezzi_iniziali_sottostanti': 'prezzi_iniziali_sottostanti', # Nuovo campo
            'note_barriere': 'note_barriere', # Nuovo campo
        }
        
        # Carica PRIMA airbag_feature, POI airbag_level, POI airbag_notes
        # Carica airbag_feature prima di tutto il resto
        if 'airbag_feature' in self.fields and 'airbag_feature' in field_mapping and field_mapping['airbag_feature'] in self.existing_data:
            value = self.existing_data[field_mapping['airbag_feature']]
            value = str(value)
            try:
                self.fields['airbag_feature'].set(value)
            except Exception as e:
                print(f"⚠️ Errore caricamento campo airbag_feature: {e}")

        self._toggle_airbag_level_field()  # Solo abilitazione/disabilitazione, non svuota

        # Poi carica airbag_level
        if 'airbag_level' in self.fields and 'airbag_level' in field_mapping and field_mapping['airbag_level'] in self.existing_data:
            value = self.existing_data[field_mapping['airbag_level']]
            print(type(self.fields['airbag_level']))
            if isinstance(value, (int, float)):
                value_to_display = value * 100 if value <= 1.0 and value != 0 else value
                value = f"{value_to_display:.2f}"
            try:
                self.fields['airbag_level'].delete(0, tk.END)
                self.fields['airbag_level'].insert(0, str(value))
            except Exception as e:
                print(f"⚠️ Errore caricamento campo airbag_level: {e}")

        # Poi carica airbag_notes
        if 'airbag_notes' in self.fields and 'airbag_notes' in field_mapping and field_mapping['airbag_notes'] in self.existing_data:
            value = self.existing_data[field_mapping['airbag_notes']]
            print(type(self.fields['airbag_notes']))
            try:
                self.fields['airbag_notes'].delete('1.0', tk.END)
                self.fields['airbag_notes'].insert('1.0', str(value))
            except Exception as e:
                print(f"⚠️ Errore caricamento campo airbag_notes: {e}")

        # Dopo il caricamento, se la feature è False, svuota i campi e disabilita
        airbag_feature_val = self.fields['airbag_feature'].get().lower()
        if airbag_feature_val == 'false':
            self._toggle_airbag_level_field(clear_on_disable=True)

        # Carica tutti gli altri campi (escludendo quelli già gestiti sopra)
        for field_name, data_key in field_mapping.items():
            if field_name in ['airbag_feature', 'airbag_level', 'airbag_notes']:
                continue
            if field_name in self.fields and data_key in self.existing_data:
                value = self.existing_data[data_key]
                
                # Conversioni speciali
                if field_name == 'memory_feature':
                    value = str(value)
                elif field_name == 'observation_delay_months' and isinstance(value, (int, float)):
                    value = str(int(value))
                elif field_name in ['coupon_rate', 'coupon_barrier', 'capital_barrier', 'dynamic_barrier_end_level', 'step_down_rate'] and isinstance(value, (int, float)):
                    value_to_display = value * 100 if value <= 1.0 and value !=0 else value
                    if field_name == 'coupon_rate':
                        value = f"{value_to_display:.3f}"
                    else:
                        value = f"{value_to_display:.2f}"
                elif field_name == 'capital_barrier_type' and self.existing_data.get('dynamic_barrier_feature', False):
                    value = 'dynamic'
                try:
                    if hasattr(self.fields[field_name], 'set'):
                        self.fields[field_name].set(str(value))
                    elif field_name == 'note_barriere':
                        self.fields['note_barriere'].delete('1.0', tk.END)
                        self.fields['note_barriere'].insert('1.0', str(value))
                    else:
                        self.fields[field_name].delete(0, tk.END)
                        self.fields[field_name].insert(0, str(value))
                except Exception as e:
                    print(f"⚠️ Errore caricamento campo {field_name}: {e}")

        # *** CARICAMENTO SPECIALE RISK-FREE RATE ***
        self.fields['risk_free_rate'].delete(0, tk.END)
        self.fields['risk_free_rate'].insert(0, f"{risk_free_percentage:.2f}")

        # *** CARICAMENTO SPECIALE AIRBAG LEVEL (solo se il campo è abilitato) ***
        airbag_level = self.existing_data.get('airbag_level', None)
        if airbag_level is not None and 'airbag_level' in self.fields:
            # Assicurati che il campo sia abilitato prima di inserire il valore
            self.fields['airbag_level'].config(state=tk.NORMAL)
            try:
                if isinstance(airbag_level, (int, float)) and airbag_level <= 1.0 and airbag_level != 0:
                    airbag_level_display = airbag_level * 100
                else:
                    airbag_level_display = airbag_level
                self.fields['airbag_level'].delete(0, tk.END)
                self.fields['airbag_level'].insert(0, f"{airbag_level_display:.2f}")
            except Exception as e:
                print(f"⚠️ Errore caricamento speciale airbag_level: {e}")

        # Aggiorna stato finale dei campi airbag
        self._toggle_airbag_level_field()
        self._on_capital_barrier_type_changed()
        self._update_dependency_description()

        print(f"✅ Dati esistenti caricati, Risk-Free Rate: {risk_free_percentage:.2f}%")
    
    def _save_v15_1_corrected(self):
        """*** SALVATAGGIO v15.1 CORRECTED *** - Con fix Risk-Free Rate e validazione completa"""
        
        print("💾 === INIZIO SALVATAGGIO v15.1 CORRECTED ===")
        
        result_data = {}
        raw_values = {} # Per memorizzare tutti i valori grezzi (stringhe) prima della conversione
        
        # Validazione campi obbligatori
        required_fields = ['isin', 'name', 'issue_date', 'maturity_date']
        for field in required_fields:
            if field in self.fields:
                value = self.fields[field].get().strip()
                if not value:
                    messagebox.showerror("Errore", f"Il campo '{field}' è obbligatorio.")
                    self.fields[field].focus()
                    return
        
        print("✅ Validazione campi base OK")
        
        # Step 1: Estrai tutti i valori grezzi (stringhe) dai campi della GUI
        for field_name, widget in self.fields.items():
            if field_name in ['airbag_notes', 'note_barriere']:
                value = widget.get('1.0', tk.END).strip()
                raw_values[field_name] = value
                continue
            if hasattr(widget, 'get'):
                raw_values[field_name] = widget.get().strip()
        
        # Step 2: Processa e converti i valori in base alla logica e alle condizioni
        for field_name, value in raw_values.items():
            if not value and field_name not in ['airbag_notes', 'note_barriere']:
                continue
            try:
                # Conversioni speciali
                if field_name == 'risk_free_rate':
                    rf_value = float(value)
                    result_data[field_name] = rf_value / 100.0
                elif field_name == 'coupon_rate':
                    cr_value = float(value)
                    result_data[field_name] = cr_value / 100.0
                elif field_name in ['coupon_barrier', 'capital_barrier', 'airbag_level']:
                    perc_value = float(value)
                    result_data[field_name] = perc_value / 100.0 if perc_value > 1 else perc_value
                elif field_name in ['step_down_rate', 'dynamic_barrier_end_level', 'observation_delay_months']:
                    # Processa questi campi SOLO se il tipo di barriera capitale è 'dynamic'
                    if raw_values.get('capital_barrier_type') == 'dynamic':
                        if field_name == 'observation_delay_months':
                            result_data[field_name] = int(value)
                        else:
                            result_data[field_name] = float(value) / 100.0
                    # Altrimenti, non aggiungere questi campi a result_data; verranno rimossi dalla logica di pop successiva
                elif field_name in ['memory_feature', 'airbag_feature']:
                    result_data[field_name] = value.lower() == 'true'
                elif field_name == 'notional':
                    result_data[field_name] = float(value)
                # Tutti gli altri campi sono trattati come stringhe
                else:
                    result_data[field_name] = value
            
            except ValueError:
                # Gestisce errori di conversione per float() e int()
                print(f"⚠️ Errore di conversione per il campo '{field_name}': il valore '{value}' non è un numero valido.")
                messagebox.showerror("Errore di Input", f"Il valore '{value}' per il campo '{field_name}' non è valido. Inserire un numero corretto.")
                return # Interrompe il processo di salvataggio
            except Exception as e:
                # Gestisce qualsiasi altro errore imprevisto durante l'elaborazione del campo
                print(f"⚠️ Errore generico durante l'elaborazione del campo '{field_name}': {e}")
                messagebox.showerror("Errore", f"Errore imprevisto nel campo '{field_name}':\n{e}")
                return

        # Logica post-estrazione
        # Imposta 'dynamic_barrier_feature' e pulisce i campi non necessari
        if result_data.get('capital_barrier_type') == 'dynamic':
            # Usa il valore della Barriera Capitale come livello iniziale per la barriera dinamica
            if 'capital_barrier' in result_data:
                result_data['dynamic_barrier_start_level'] = result_data['capital_barrier']
            result_data['dynamic_barrier_feature'] = True
        else:
            result_data['dynamic_barrier_feature'] = False
            # Rimuovi i campi dinamici se il tipo di barriera non è 'dynamic'
            for key in ['dynamic_barrier_start_level', 'step_down_rate', 'dynamic_barrier_end_level', 'observation_delay_months']:
                result_data.pop(key, None)
        
        # Validazione coerenza airbag
        if result_data.get('airbag_feature', False) and not result_data.get('airbag_level'):
            messagebox.showerror("Errore", "Specificare il livello dell'airbag se la feature è abilitata.")
            return
        
        print(f"✅ Estrazione dati completata: {len(result_data)} campi.")
        print(f"📊 Risk-Free Rate finale: {result_data.get('risk_free_rate', 'N/A')}")
        
        # Salva e chiudi
        self.result = result_data
        self.dialog.destroy()
        
        print("💾 === SALVATAGGIO v15.1 CORRECTED COMPLETATO ===")
     
    
    def _cancel(self):
        """Annulla dialog v15.1 CORRECTED"""
        print("❌ Dialog v15.1 CORRECTED annullato dall'utente")
        self.result = None
        self.dialog_closed = True
        self.dialog.destroy()

    def _toggle_airbag_level_field(self, event=None, clear_on_disable=False):
        """Abilita/disabilita il campo Livello Airbag e Note Airbag in base alla selezione di Airbag Feature."""
        if hasattr(self, 'fields') and 'airbag_feature' in self.fields and 'airbag_level' in self.fields and 'airbag_notes' in self.fields:
            airbag_enabled = self.fields['airbag_feature'].get().lower() == 'true'
            if airbag_enabled:
                self.fields['airbag_level'].config(state=tk.NORMAL)
                self.airbag_level_label.config(state=tk.NORMAL)
                self.fields['airbag_notes'].config(state=tk.NORMAL)
                self.airbag_notes_label.config(state=tk.NORMAL)
            else:
                self.fields['airbag_level'].config(state=tk.DISABLED)
                self.airbag_level_label.config(state=tk.DISABLED)
                self.fields['airbag_notes'].config(state=tk.DISABLED)
                self.airbag_notes_label.config(state=tk.DISABLED)
                # Pulizia sempre dei campi airbag se disabilitato
                self.fields['airbag_level'].delete(0, tk.END)
                self.fields['airbag_notes'].delete('1.0', tk.END)

    def _on_capital_barrier_type_changed(self, event=None):
        """Abilita/disabilita i campi della barriera dinamica in base alla selezione del tipo di barriera capitale."""
        if hasattr(self, 'fields') and 'capital_barrier_type' in self.fields and hasattr(self, 'dynamic_barrier_params_frame'):
            selected_type = self.fields['capital_barrier_type'].get()
            is_dynamic = (selected_type == 'dynamic')

            if is_dynamic:
                self.dynamic_barrier_params_frame.pack(fill='x', padx=10, pady=5)
                # --- Mostra e precompila Livello Iniziale con valore Barriera Capitale ---
                if 'dynamic_barrier_start_level' in self.fields and 'capital_barrier' in self.fields:
                    capital_barrier_val = self.fields['capital_barrier'].get().strip()
                    self.fields['dynamic_barrier_start_level'].config(state=tk.NORMAL)
                    self.fields['dynamic_barrier_start_level'].delete(0, tk.END)
                    if capital_barrier_val:
                        self.fields['dynamic_barrier_start_level'].insert(0, capital_barrier_val)
                # Abilita anche gli altri campi dinamici
                for field_name in ['step_down_rate', 'dynamic_barrier_end_level']:
                    if field_name in self.fields:
                        self.fields[field_name].config(state=tk.NORMAL)
            else:
                self.dynamic_barrier_params_frame.pack_forget()
                # Disabilita e svuota tutti i campi dinamici
                for field_name in ['dynamic_barrier_start_level', 'step_down_rate', 'dynamic_barrier_end_level']:
                    if field_name in self.fields:
                        self.fields[field_name].config(state=tk.DISABLED)
                        self.fields[field_name].delete(0, tk.END)

    def _update_dependency_description(self, event=None):
        """Aggiorna la descrizione del tipo di dipendenza sottostante."""
        if hasattr(self, 'fields') and 'underlying_dependency_type' in self.fields:
            selected_type = self.fields['underlying_dependency_type'].get()
            description = self._dependency_descriptions.get(selected_type, "Descrizione non disponibile.")
            # Usa textwrap per formattare la descrizione
            formatted_description = textwrap.fill(description, width=100) # Larghezza per andare a capo
            self.dependency_description_label.config(text=formatted_description)


# ========================================
# GUI MANAGER v15.1 CORRECTED - CON CALC DATE INTEGRATA E FIX REALCONFIG
# ========================================

class SimpleCertificateGUIManagerV15_1_Corrected:
    """*** GUI MANAGER v15.1 CORRECTED *** - Con calc date integrata e correzioni complete"""
    
    # Mappa descrizioni per Tipo Dipendenza - DEFINITO COME ATTRIBUTO DI CLASSE
    _dependency_descriptions = {
        'Worst-Of': "🔻 WORST-OF: Il peggiore tra tutti determina il payoff (MASSIMO RISCHIO). Performance = MIN(asset1, asset2, asset3, ...) - Basta che uno crolli!",
        'Best-Of': "🔺 BEST-OF: Il migliore tra tutti determina il payoff (MINIMO RISCHIO). Performance = MAX(asset1, asset2, asset3, ...) - Uno solo deve andare bene.",
        'Average': "📈 AVERAGE/BASKET: Performance media ponderata (RISCHIO INTERMEDIO). Performance = MEDIA(asset1, asset2, asset3, ...) - Compensazione reciproca.",
        'Single': "🌈 RAINBOW/INDIVIDUAL: Ogni asset contribuisce individualmente. Payoff calcolato per singolo sottostante - Struttura complessa.", # Mappato a Rainbow
        'Basket Custom': "🌈 RAINBOW/INDIVIDUAL: Ogni asset contribuisce individualmente. Payoff calcolato per singolo sottostanti - Struttura complessa." # Mappato a Rainbow
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema Certificati v15.1 CORRECTED")
        self.root.geometry("1400x900")
        
        # Variabili
        self.certificates = {}
        self.cert_file = Path("certificates_v15_1_corrected.json")
        
        # Enhanced manager per calc date
        if ENHANCED_MANAGER_AVAILABLE:
            try:
                self.enhanced_manager = EnhancedCertificateManagerV15()
                print("✅ Enhanced Manager v15 inizializzato per calc date")
            except Exception as e:
                print(f"⚠️ Enhanced Manager non disponibile: {e}")
                self.enhanced_manager = None
        else:
            self.enhanced_manager = None
        
        # *** PORTFOLIO MANAGER INTEGRATION v15.1 ***
        # Istanziamo PortfolioManager e PortfolioGUIManager direttamente qui
        try:
            from portfolio_manager import PortfolioManager, PortfolioGUIManager # Assicurati che sia importato
            self.portfolio_manager = PortfolioManager(self.cert_file.parent if self.cert_file else Path("."))
            # Passa una lista di dicts per i certificati, non l'oggetto EnhancedCertificateConfig
            # Questo è un placeholder, la gestione reale dei certificati nel portfolio manager
            # dovrebbe essere più robusta e probabilmente caricare i certificati dal manager stesso.
            self.portfolio_gui = PortfolioGUIManager(self.portfolio_manager, self.root, list(self.certificates.values())) 
            print("✅ Portfolio Manager e GUI Manager inizializzati direttamente nella GUI principale.")
        except ImportError as e:
            print(f"⚠️ Portfolio Manager non disponibile per importazione diretta: {e}")
            self.portfolio_manager = None # Imposta a None se l'import fallisce
            self.portfolio_gui = None   # Imposta a None se l'import fallisce

        # Carica certificati esistenti
        self.certificates = self._load_certificates()
        
        # Setup GUI
        self._setup_gui_v15_1_corrected()
        
        # Refresh lista
        self._refresh_certificate_list()
        
        print("🚀 === GUI MANAGER v15.1 CORRECTED INIZIALIZZATO ===")
    
    def _setup_gui_v15_1_corrected(self):
        """Setup GUI completa v15.1 CORRECTED"""
        
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(toolbar, text="➕ Nuovo Certificato", 
                  command=self._new_certificate).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="✏️ Modifica", 
                  command=self._edit_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="🗑️ Elimina", 
                  command=self._delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        
        # *** FIX CALC DATE v15.1 *** - Pulsante con funzione integrata
        if self.enhanced_manager:
            ttk.Button(toolbar, text="📅 Calc Date v15.1", 
                      command=self._calculate_dates_integrated).pack(side=tk.LEFT, padx=(0, 5))
        else:
            ttk.Button(toolbar, text="📅 Calc Date (non disponibile)", 
                      state="disabled").pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toolbar, text="📊 Analizza", 
                  command=self._analyze_selected).pack(side=tk.LEFT, padx=(0, 5))
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(toolbar, text="💾 Salva Tutti", 
                  command=self._save_certificates).pack(side=tk.LEFT, padx=(0, 5))
        #ttk.Button(toolbar, text="🔄 Ricarica", 
        #          command=self._reload_certificates).pack(side=tk.LEFT)
        
        # *** NUOVO v15.1 *** - Pulsante Portfolio Manager
        if hasattr(self, 'portfolio_gui') and self.portfolio_gui is not None:
            ttk.Button(toolbar, text="📁 Portfolio Manager",
                       command=self._open_portfolio_manager).pack(side=tk.LEFT, padx=(10, 5))
        else:
            print("⚠️  Portfolio Manager non disponibile. Pulsante disabilitato.")
            ttk.Button(toolbar, text="📁 Portfolio Manager (non disponibile)", state="disabled").pack(side=tk.LEFT, padx=(10, 5))
        
        # Pulsanti di sistema a destra
        system_buttons_frame = ttk.Frame(toolbar)
        system_buttons_frame.pack(side=tk.RIGHT, padx=(20,0))
        ttk.Button(system_buttons_frame, text="🚪 Esci", command=self.close).pack(side=tk.LEFT)


        # Main content
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Paned window
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Lista certificati
        list_frame = ttk.LabelFrame(paned, text="📋 Certificati")
        paned.add(list_frame, weight=1)
        
        # Tree view
        columns = ("ISIN", "Nome", "Tipo", "Emittente", "Risk-Free %", "Scadenza")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "ISIN":
                self.tree.column(col, width=120)
            elif col == "Nome":
                self.tree.column(col, width=200)
            elif col == "Risk-Free %":
                self.tree.column(col, width=100)
            else:
                self.tree.column(col, width=120)
        
        # Scrollbar lista
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=list_scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind eventi
        self.tree.bind("<Double-1>", self._edit_selected)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        
        # Dettagli certificato
        details_frame = ttk.LabelFrame(paned, text="📊 Dettagli Certificato")
        paned.add(details_frame, weight=1)
        
        # Text widget con scrollbar
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.details_text = tk.Text(text_frame, wrap=tk.WORD, font=("Courier", 10))
        details_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Sistema Certificati v15.1 CORRECTED - Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # *** NUOVO METODO v15.1 *** - Apre la finestra del Portfolio Manager
    def _open_portfolio_manager(self):
        """Apre la finestra del Portfolio Manager."""
        if not hasattr(self, 'portfolio_gui') or self.portfolio_gui is None:
            messagebox.showerror("Errore", "Portfolio Manager non inizializzato.")
            return

        try:
            # Aggiorna i certificati nel PortfolioGUIManager prima di aprirlo
            # Questo è fondamentale per assicurare che il PM abbia i dati più recenti
            self.portfolio_gui.update_certificates_data(self.certificates)
            self.portfolio_gui.create_portfolio_dashboard_window()

            print("📁 Finestra Portfolio Manager aperta.")

        except Exception as e:
            print(f"❌ Errore nell'apertura del Portfolio Manager: {e}")
            messagebox.showerror("Errore Portfolio Manager", f"Impossibile aprire il Portfolio Manager:\n{e}")    


    def _calculate_dates_integrated(self):
        """*** CALC DATE INTEGRATA v15.1 CORRECTED *** - Funzione completamente operativa"""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato per calcolare le date")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]
        
        if cert_id not in self.certificates:
            messagebox.showerror("Errore", f"Certificato {cert_id} non trovato")
            return
        
        print(f"📅 === CALC DATE INTEGRATA v15.1 CORRECTED per {cert_id} ===")
        
        try:
            if self.enhanced_manager:
                # Usa enhanced manager
                cert_data = copy.deepcopy(self.certificates[cert_id])
                # --- AGGIUNTA: assicurati che i parametri dinamici siano coerenti ---
                if cert_data.get('capital_barrier_type') == 'dynamic' or cert_data.get('dynamic_barrier_feature'):
                    # Se mancano i parametri dinamici, prova a recuperarli da capital_barrier ecc.
                    if 'dynamic_barrier_start_level' not in cert_data and 'capital_barrier' in cert_data:
                        cert_data['dynamic_barrier_start_level'] = cert_data['capital_barrier']
                    if 'step_down_rate' not in cert_data:
                        cert_data['step_down_rate'] = 0.0
                    if 'dynamic_barrier_end_level' not in cert_data:
                        cert_data['dynamic_barrier_end_level'] = 0.0
                    if 'observation_delay_months' not in cert_data:
                        cert_data['observation_delay_months'] = 0
                # --- FINE AGGIUNTA ---

                # Apri dialog calc date v15
                dialog = CalculoDateAutoDialogV15(
                    self.root, 
                    selected_certificate_id=cert_id,
                    configurations={cert_id: cert_data}
                )
                
                # *** FIX CRITICO ***: Attende che il dialog sia chiuso prima di procedere
                self.root.wait_window(dialog.dialog)
                
                if hasattr(dialog, 'result') and dialog.result:
                    print(f"📅 Date calcolate per {cert_id}")
                    
                    # Aggiorna certificato
                    self.certificates[cert_id].update(dialog.result)
                    
                    # Salva
                    if self._save_certificates():
                        self._refresh_certificate_list()
                        # Dopo aver aggiornato la lista, ri-seleziona il certificato modificato
                        # Trova l'elemento nel treeview tramite il suo ISIN
                        for item_id in self.tree.get_children():
                            if self.tree.item(item_id, 'values')[0] == cert_id:
                                self.tree.selection_set(item_id)
                                self.tree.focus(item_id)
                                break
                        self._display_certificate_details(cert_id)
                        messagebox.showinfo("Successo", f"Date calcolate e salvate per {cert_id}!")
                    else:
                        messagebox.showerror("Errore", "Errore salvataggio date calcolate")
                else:
                    print("📅 Calc date annullata dall'utente")
            else:
                messagebox.showerror("Errore", "Enhanced Manager non disponibile per calc date")
                
        except Exception as e:
            print(f"❌ Errore calc date integrata: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Errore", f"Errore calcolo date:\n{e}")
    
    def _new_certificate(self):
        """Nuovo certificato con dialog v15.1 CORRECTED"""
        
        print("➕ === NUOVO CERTIFICATO v15.1 CORRECTED ===")
        
        try:
            dialog = EnhancedCertificateDialogV15_1_Corrected(self.root, "Nuovo Certificato")
            
            if hasattr(dialog, 'result') and dialog.result:
                cert_data = dialog.result
                cert_id = cert_data['isin']
                
                print(f"💾 Creazione certificato {cert_id}")
                print(f"📊 Risk-Free Rate: {cert_data.get('risk_free_rate', 'N/A')}")
                
                # Verifica non esistente
                if cert_id in self.certificates:
                    if not messagebox.askyesno("ISIN Esistente", 
                                             f"Certificato {cert_id} già esistente. Sovrascrivere?"):
                        return
                
                # Salva certificato
                self.certificates[cert_id] = cert_data
                
                if self._save_certificates():
                    self._refresh_certificate_list()
                    # Dopo aver aggiornato la lista, seleziona il nuovo certificato
                    # Trova l'elemento nel treeview tramite il suo ISIN
                    for item_id in self.tree.get_children():
                        if self.tree.item(item_id, 'values')[0] == cert_id:
                            self.tree.selection_set(item_id)
                            self.tree.focus(item_id)
                            break
                    messagebox.showinfo("Successo", f"Certificato {cert_id} creato con successo!")
                    print(f"✅ Certificato {cert_id} creato e salvato")
                else:
                    print(f"❌ Errore salvataggio certificato {cert_id}")
                    messagebox.showerror("Errore", f"Impossibile salvare certificato {cert_id}")
            else:
                print("ℹ️ Dialog nuovo certificato annullato")
                
        except Exception as e:
            print(f"❌ Errore nuovo certificato: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Errore", f"Errore creazione certificato:\n{e}")
    
    def _edit_selected(self, event=None):
        """Modifica certificato con dialog v15.1 CORRECTED"""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da modificare")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]
        
        if cert_id not in self.certificates:
            messagebox.showerror("Errore", f"Certificato {cert_id} non trovato")
            return
        
        # Backup dati originali
        cert_data_original = copy.deepcopy(self.certificates[cert_id])
        print(f"✏️ === MODIFICA CERTIFICATO {cert_id} v15.1 CORRECTED ===")
        print(f"📊 Risk-Free Rate originale: {cert_data_original.get('risk_free_rate', 'N/A')}")
        
        try:
            dialog = EnhancedCertificateDialogV15_1_Corrected(self.root, f"Modifica {cert_id}", cert_data_original)
            
            if hasattr(dialog, 'result') and dialog.result:
                updated_data = dialog.result
                print(f"📊 Risk-Free Rate aggiornato: {updated_data.get('risk_free_rate', 'N/A')}")
                
                # Verifica ISIN non cambiato
                if updated_data['isin'] != cert_id:
                    if messagebox.askyesno("ISIN Modificato", 
                                         f"ISIN cambiato da {cert_id} a {updated_data['isin']}. Procedere?"):
                        # Rimuovi vecchio ISIN
                        del self.certificates[cert_id]
                        cert_id = updated_data['isin']
                    else:
                        updated_data['isin'] = cert_id  # Ripristina ISIN originale
                
                # Salva modifiche
                self.certificates[cert_id] = updated_data
                
                if self._save_certificates():
                    self._refresh_certificate_list()
                    self._display_certificate_details(cert_id)

                    # Dopo aver aggiornato la lista, ri-seleziona il certificato modificato
                    # Trova l'elemento nel treeview tramite il suo ISIN
                    for item_id in self.tree.get_children():
                        if self.tree.item(item_id, 'values')[0] == cert_id:
                            self.tree.selection_set(item_id)
                            self.tree.focus(item_id)
                            break                    
                    messagebox.showinfo("Successo", f"Certificato {cert_id} modificato con successo!")
                    print(f"✅ Certificato {cert_id} modificato e salvato")
                else:
                    print(f"❌ Errore salvataggio, rollback")
                    self.certificates[cert_id] = cert_data_original  # Rollback
                    messagebox.showerror("Errore", f"Impossibile salvare modifiche a {cert_id}")
            else:
                print(f"❌ Dialog certificato v15.1 CORRECTED annullato dall'utente")
                
        except Exception as e:
            print(f"❌ Errore modifica certificato, rollback: {e}")
            self.certificates[cert_id] = cert_data_original  # Rollback
            import traceback
            traceback.print_exc()
            messagebox.showerror("Errore", f"Errore modifica certificato:\n{e}")
    
    def _refresh_certificate_list(self):
        """Refresh lista certificati con Risk-Free Rate corretto"""
        
        # Pulisci tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Aggiungi certificati
        for cert_id, cert_data in self.certificates.items():
            if cert_data:
                # *** FIX DISPLAY RISK-FREE RATE v15.1 ***
                risk_free_rate = cert_data.get('risk_free_rate', 0)
                if isinstance(risk_free_rate, (int, float)):
                    if risk_free_rate <= 1.0:  # Formato decimale
                        rf_display = f"{risk_free_rate * 100:.2f}%"
                    else:  # Già percentuale
                        rf_display = f"{risk_free_rate:.2f}%"
                else:
                    rf_display = str(risk_free_rate)
                
                self.tree.insert("", tk.END, values=(
                    cert_id,
                    cert_data.get('name', 'N/A'),
                    cert_data.get('certificate_type', 'N/A'),
                    cert_data.get('issuer', 'N/A'),
                    rf_display,  # Risk-Free Rate formattato
                    cert_data.get('maturity_date', 'N/A')
                ))
        
        # Status update
        count = len(self.certificates)
        self.status_var.set(f"Sistema Certificati v15.1 CORRECTED - {count} certificati caricati")
    
    def _on_selection_changed(self, event=None):
        """Gestione selezione certificato"""
        selection = self.tree.selection()
        if selection:
            cert_id = self.tree.item(selection[0])['values'][0]
            self._display_certificate_details(cert_id)
    
    def _display_certificate_details(self, cert_id):
        """*** DISPLAY DETTAGLI v15.1 CORRECTED *** - Con Risk-Free Rate corretto"""
        
        if cert_id not in self.certificates:
            return
        
        cert_data = self.certificates[cert_id]

        # *** FORMATTAZIONE RISK-FREE RATE CORRETTA ***
        risk_free_rate = cert_data.get('risk_free_rate', 0)
        if isinstance(risk_free_rate, (int, float)):
            if risk_free_rate <= 1.0:  # Formato decimale
                rf_display = f"{risk_free_rate * 100:.2f}%"
            else:
                rf_display = f"{risk_free_rate:.2f}%"
        else:
            rf_display = str(risk_free_rate)
        
        # Formatta altri campi percentuali
        def format_percentage(value, decimals=2):
            if isinstance(value, (int, float)):
                if value <= 1.0:
                    return f"{value * 100:.{decimals}f}%"
                else:
                    return f"{value:.{decimals}f}%"
            return str(value)
        
        # --- AIRBAG: mostra N/A se disattivato, mostra note se presenti ---
        airbag_feature = cert_data.get('airbag_feature', 'N/A')
        if airbag_feature is True or (isinstance(airbag_feature, str) and airbag_feature.lower() == 'true'):
            airbag_level_str = format_percentage(cert_data.get('airbag_level', 0))
            airbag_notes = cert_data.get('airbag_notes', '').strip()
        else:
            airbag_level_str = "N/A"
            airbag_notes = ""

        prezzi_iniziali = cert_data.get('prezzi_iniziali_sottostanti', 'N/A')
        note_barriere = cert_data.get('note_barriere', '').strip()

        # Formatta prezzi_iniziali per visualizzazione con separatore migliaia
        def format_prezzi_iniziali(val):
            if not val or val == 'N/A':
                return 'N/A'
            try:
                # Supporta lista di valori separati da virgola
                parts = [x.strip() for x in str(val).split(',')]
                formatted = []
                for p in parts:
                    # Sostituisci eventuali punti con niente (per chi inserisce 1.234,56)
                    p_clean = p.replace('.', '').replace(' ', '').replace("'", "")
                    # Sostituisci virgola con punto per float
                    p_clean = p_clean.replace(',', '.')
                    num = float(p_clean)
                    formatted.append(f"{num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                return ', '.join(formatted)
            except Exception:
                return val

        details = f"""DETTAGLI CERTIFICATO v15.1 CORRECTED
{'='*60}

INFORMAZIONI BASE:
ISIN: {cert_data.get('isin', 'N/A')}
Nome Certificato: {cert_data.get('name', 'N/A')}
Ticker Strumento: {cert_data.get('certificate_instrument_ticker', 'N/A')}
Tipo Certificato: {cert_data.get('certificate_type', 'N/A')}
Emittente: {cert_data.get('issuer', 'N/A')}

DATE E PARAMETRI:
Data Emissione: {cert_data.get('issue_date', 'N/A')}
Data Scadenza: {cert_data.get('maturity_date', 'N/A')}
Nominale: €{cert_data.get('notional', 0):,.2f}

TASSI:
Risk-Free Rate: {rf_display}
Tasso Cedola Periodico: {format_percentage(cert_data.get('coupon_rate', 0), decimals=3)}
Frequenza Cedola: {cert_data.get('coupon_frequency', 'N/A')}

CARATTERISTICHE:
Effetto Memoria: {cert_data.get('memory_feature', 'N/A')}
Airbag: {airbag_feature}
Livello Airbag: {airbag_level_str}
"""
        if airbag_notes:
            details += f"Note Airbag: {airbag_notes}\n"

        details += f"""
BARRIERE:
Barriera Cedola: {format_percentage(cert_data.get('coupon_barrier', 0))} ({cert_data.get('coupon_barrier_type', 'N/A')})
Barriera Capitale: {format_percentage(cert_data.get('capital_barrier', 0))} ({cert_data.get('capital_barrier_type', 'N/A')})
"""
        if note_barriere:
            details += f"Note Barriere: {note_barriere}\n"

        details += f"""
BARRIERE DINAMICHE:
Abilitata: {cert_data.get('dynamic_barrier_feature', 'N/A')}{' (Livello Iniziale = Barriera Capitale)' if cert_data.get('dynamic_barrier_feature') else ''}
{f'''
Livello Iniziale: {format_percentage(cert_data.get('dynamic_barrier_start_level', 0))}
Step Down Rate: {format_percentage(cert_data.get('step_down_rate', 0), decimals=3)}
Livello Finale: {format_percentage(cert_data.get('dynamic_barrier_end_level', 0))}
Mesi di Ritardo Osservazione: {cert_data.get('observation_delay_months', 'N/A')}
''' if cert_data.get('dynamic_barrier_feature') else ''}

SOTTOSTANTI:
Tickers Sottostanti (Yahoo): {cert_data.get('yahoo_ticker', 'N/A')}
Prezzi Iniziali/Strike: {format_prezzi_iniziali(prezzi_iniziali)}
Nomi/Desc Sottostanti: {cert_data.get('underlying_names', 'N/A')}
Valute Sottostanti: {cert_data.get('underlying_currencies', 'N/A')}
Tipo Dipendenza Sottostanti: {cert_data.get('underlying_dependency_type', 'N/A')}
"""
        # Aggiungi descrizione della dipendenza se disponibile (usa self._dependency_descriptions)
        dependency_type = cert_data.get('underlying_dependency_type')
        if dependency_type and dependency_type in self._dependency_descriptions:
            details += f"Descrizione Dipendenza: {self._dependency_descriptions[dependency_type]}\n"
        
        details += f"""
Valuta Certificato: {cert_data.get('currency', 'N/A')}

DATI AVANZATI:
Date Cedole: {len(cert_data.get('coupon_dates', []))} date
Autocall Levels: {len(cert_data.get('autocall_levels', []))} livelli
"""
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
    
    def _load_certificates(self):
        """*** CARICAMENTO CERTIFICATI v15.1 CORRECTED *** - Con conversione campi v15.1 e gestione nuovi campi"""
        
        if not self.cert_file.exists():
            print(f"ℹ️ File {self.cert_file} non esiste, inizializzazione vuota")
            return {}
        
        try:
            with open(self.cert_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📂 Caricamento {len(data)} certificati...")
            
            # Gestisce formato enhanced e basic
            certificates = {}
            for cert_id, cert_data in data.items():
                try:
                    # Determine the actual config dictionary to work with
                    # If it's an enhanced format, use base_config, otherwise use cert_data itself
                    if 'base_config' in cert_data:
                        config_to_process = cert_data['base_config']
                    else:
                        config_to_process = cert_data

                    # Ensure coupon_dates, coupon_rates, autocall_levels are lists, even if missing or None
                    if 'coupon_dates' not in config_to_process or config_to_process['coupon_dates'] is None:
                        config_to_process['coupon_dates'] = []
                    if 'coupon_rates' not in config_to_process or config_to_process['coupon_rates'] is None:
                        config_to_process['coupon_rates'] = []
                    if 'autocall_levels' not in config_to_process or config_to_process['autocall_levels'] is None:
                        config_to_process['autocall_levels'] = []

                    # *** CONVERSIONE v15.1 CORRECTED ***
                    # Converte campi v15.1 nel formato compatibile se necessario
                    if any(field in config_to_process for field in ['coupon_barrier_type', 'capital_barrier_type', 'dynamic_barrier_feature']): # This line was duplicated, but the logic is now correct.
                        print(f"🔄 Conversion v15.1 for {cert_id}")
                        processed_config = self._convert_v15_1_fields(config_to_process)
                        certificates[cert_id] = processed_config
                    else:
                        certificates[cert_id] = config_to_process

                except Exception as e:
                    print(f"⚠️ Errore caricamento {cert_id}: {e}")
                    # Mantieni dati originali anche se problematici
                    certificates[cert_id] = cert_data
            
            print(f"✅ Caricati {len(certificates)} certificati da {self.cert_file}")
            return certificates
            
        except Exception as e:
            print(f"⚠️ Errore caricamento certificati: {e}")
            messagebox.showerror("Errore Caricamento", 
                               f"Errore caricamento certificati:\n{e}\n\nCreando nuovo file...")
            return {}
    
    def _convert_v15_1_fields(self, cert_data):
        """*** CONVERSIONE CAMPI v15.1 *** - Mantiene compatibilità per salvataggio"""
        
        converted = cert_data.copy()
        
        # Converte barriere v15.1 in formato legacy per compatibilità display
        barrier_levels = {}
        
        if 'coupon_barrier_value' in cert_data and cert_data['coupon_barrier_value']:
            barrier_levels['coupon'] = cert_data['coupon_barrier_value']
        
        if 'capital_barrier_value' in cert_data and cert_data['capital_barrier_value']:
            barrier_levels['capital'] = cert_data['capital_barrier_value']
        
        if 'airbag_level' in cert_data and cert_data.get('airbag_feature'):
            barrier_levels['airbag'] = cert_data['airbag_level']

        # Gestione nuovi campi barriera dinamica
        if 'dynamic_barrier_feature' in cert_data:
            converted['dynamic_barrier_feature'] = cert_data['dynamic_barrier_feature']
            converted['dynamic_barrier_start_level'] = cert_data.get('dynamic_barrier_start_level')
            converted['step_down_rate'] = cert_data.get('step_down_rate')
            converted['dynamic_barrier_end_level'] = cert_data.get('dynamic_barrier_end_level')

        if barrier_levels:
            converted['barrier_levels'] = barrier_levels
        
        return converted
    
    def _save_certificates(self):
        """Salva certificati"""
        
        try:
            print(f"💾 === SALVATAGGIO CERTIFICATI v15.1 CORRECTED ===")
            print(f"💾 Certificati da salvare: {len(self.certificates)}")
            
            # Crea backup
            if self.cert_file.exists():
                backup_file = self.cert_file.with_suffix('.backup')
                import shutil
                shutil.copy2(self.cert_file, backup_file)
                print(f"💾 Backup creato: {backup_file}")
            
            # Salva
            with open(self.cert_file, 'w', encoding='utf-8') as f:
                json.dump(self.certificates, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✅ Certificati salvati in {self.cert_file}")
            return True
            
        except Exception as e:
            print(f"❌ Errore salvataggio: {e}")
            messagebox.showerror("Errore Salvataggio", f"Errore salvataggio certificati:\n{e}")
            return False
    
    def _reload_certificates(self):
        """Ricarica certificati da file"""
        self.certificates = self._load_certificates()
        self._refresh_certificate_list()
        messagebox.showinfo("Ricaricato", f"Ricaricati {len(self.certificates)} certificati")
    
    def _delete_selected(self):
        """Elimina certificato selezionato"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da eliminare")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]

        
        if messagebox.askyesno("Conferma Eliminazione", 
                             f"Eliminare definitivamente il certificato {cert_id}?"):
            del self.certificates[cert_id]
            if self._save_certificates():
                self._refresh_certificate_list()
                self.details_text.delete(1.0, tk.END)
                messagebox.showinfo("Eliminato", f"Certificato {cert_id} eliminato")
    
    def _analyze_selected(self):
        """Analizza certificato selezionato"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da analizzare")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]
        messagebox.showinfo("Analisi", f"Analisi per {cert_id} - Funzionalità in sviluppo v15.1")
    
    def close(self):
        """Chiusura applicazione"""
        if messagebox.askyesno("Chiusura", "Chiudere il Sistema Certificati v15.1 CORRECTED?"):
            print("🚪 Chiusura GUI Certificate Manager v15.1 CORRECTED")
            self.root.destroy()
    
    def run(self):
        """Avvia GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()


# ========================================
# MAIN EXECUTION
# ========================================



if __name__ == "__main__":
    print("🚀 === SISTEMA CERTIFICATI v15.1 CORRECTED - AVVIO ===")
    print("✅ Correzioni v15.1 CORRECTED:")
    print("   - FIX CRITICO: Compatibilità campi v15.1 con RealCertificateConfig")
    print("   - Risk-Free Rate coordinato (formato percentuale)")
    print("   - Calc Date completamente integrata")
    print("   - Form completo con validazione")
    print("   - Conversione automatica barriere v15.1")
    print("="*70)
    
    try:
        # Avvia GUI Manager v15.1 CORRECTED
        manager = SimpleCertificateGUIManagerV15_1_Corrected()
        manager.run()
        
    except Exception as e:
        print(f"❌ Errore avvio Sistema v15.1 CORRECTED: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback
        messagebox.showerror("Errore Sistema", 
                           f"Errore critico avvio Sistema v15.1 CORRECTED:\n{e}\n\nContattare supporto tecnico")
