# ==========================================================
# NOME FILE: fixed_gui_v15_1_corrected.py
# SCOPO: Gestione GUI avanzata per inserimento, modifica e visualizzazione certificati finanziari v15.1
# AUTORE: Team di sviluppo
# DATA CREAZIONE: 2024-06-22
# ULTIMA MODIFICA: 2025-07-08 (Integrazione analisi completa)
# VERSIONE: 1.1
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
import logging
import textwrap # Per formattare la descrizione della dipendenza
from app.core.consolidated_risk_system import (
    UnifiedRiskAnalyzer, analyze_certificate_risk
)    
from app.core.real_certificate_integration import RealCertificateImporter
# --- MODIFICA ---
# Aggiunto import per UnifiedCertificateAnalyzer
from app.core.unified_certificates import UnifiedCertificateAnalyzer
# --- FINE MODIFICA ---




# Import sistema esistente
try:
    from app.core.real_certificate_integration import (
         RealCertificateConfig, IntegratedCertificateSystem
    )
    print("✅ Import sistema esistente OK")
    
    # Import enhanced manager per calc date
    try:
        from app.core.enhanced_certificate_manager_fixed import (
            EnhancedCertificateManagerV15,
            CalculoDateAutoDialogV15,  # <-- RIMUOVI questa riga se la classe non esiste più in quel file
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

# Importa moduli di analisi e reportistica
from app.core.consolidated_risk_system import UnifiedRiskAnalyzer
from app.utils.excel_enhancement_plan import AdvancedExcelExporter


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
        # Deepcopy funziona anche sugli oggetti
        self.existing_data = copy.deepcopy(existing_data) if existing_data else None
        self.dialog_closed = False
        
        print(f"📝 === APERTURA DIALOG v15.1 CORRECTED ===")
        print(f"📝 Title: {title}")
        
        # === LA CORREZIONE E' QUI ===
        if self.existing_data:
            # Controlliamo se è un oggetto RealCertificateConfig o un dizionario
            if hasattr(self.existing_data, 'isin'):
                print(f"📝 Dati esistenti per l'oggetto con ISIN: {self.existing_data.isin}")
            else:
                 # Fallback nel caso ricevessimo ancora un dizionario
                print(f"📝 Dati esistenti (dict): {list(self.existing_data.keys())}")
        else:
            print(f"📝 Nuovo certificato (form vuoto)")
        # === FINE CORREZIONE ===
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title + " - v15.1 CORRECTED")
        self.dialog.geometry("1000x900")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_dialog_close)
        
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 500
        y = (self.dialog.winfo_screenheight() // 2) - 450
        self.dialog.geometry(f"1000x900+{x}+{y}")
        
        self._setup_form_complete_v15_1_corrected()
        
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
        v_scrollbar.pack(side=tk.RIGHT, fill="y")
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
        self.fields['issue_date'].pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(row3_frame, text="(AAAA-MM-DD)", font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(2, 20)) # <-- AGGIUNTA
        
        ttk.Label(row3_frame, text="Scadenza:", width=15).pack(side=tk.LEFT)
        self.fields['maturity_date'] = ttk.Entry(row3_frame, width=12)
        self.fields['maturity_date'].pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(row3_frame, text="(AAAA-MM-DD)", font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(2, 0)) # <-- AGGIUNTA
        
        
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
        ttk.Label(fin_row1_frame, text="(es: 3.5 per 3.5%, usa '.' come decimale, valore su base annuale)", 
                 font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(5, 0))
        
        # *** NUOVO v15.1 *** - Tasso Cedola
        fin_row2_frame = ttk.Frame(financial_frame)
        fin_row2_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(fin_row2_frame, text="Tasso Cedola (% del periodo):", width=25).pack(side=tk.LEFT) 
        self.fields['coupon_rate'] = ttk.Entry(fin_row2_frame, width=10)
        self.fields['coupon_rate'].pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(fin_row2_frame, text="(es. 0.7)", font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(2, 20)) # <-- AGGIUNTA

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
        
        barriers_frame = ttk.LabelFrame(self.scrollable_frame, text="🚧 Livelli Barriera (valori %)", padding=15)
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
        ttk.Label(ticker_frame, text="Tickers Sottostanti (Yahoo, ';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['yahoo_ticker'] = ttk.Entry(ticker_frame, width=40)
        self.fields['yahoo_ticker'].pack(side=tk.LEFT, padx=(5, 20))

        # Prezzi iniziali/strike/prezzi di riferimento
        strike_frame = ttk.Frame(underlying_frame)
        strike_frame.pack(fill=tk.X, pady=5)
        ttk.Label(strike_frame, text="Prezzi Iniziali/Strike (';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['prezzi_iniziali_sottostanti'] = ttk.Entry(strike_frame, width=40)
        self.fields['prezzi_iniziali_sottostanti'].pack(side=tk.LEFT, padx=(5, 5))
        # Indicazione formato inserimento
        ttk.Label(
            strike_frame,
            text="(Formato EU:1.234,56; 57,12)", #NOTA AGGIORNATA
            font=('Arial', 8), foreground='gray'
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Nomi/Descrizioni Sottostanti
        desc_frame = ttk.Frame(underlying_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="Nomi/Desc Sottostanti (';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['underlying_names'] = ttk.Entry(desc_frame, width=60) # Larghezza aumentata
        self.fields['underlying_names'].pack(side=tk.LEFT, padx=(5,0))
        
        # Valute Sottostanti
        currency_frame = ttk.Frame(underlying_frame) # Nuovo frame per le valute
        currency_frame.pack(fill=tk.X, pady=5)

        ttk.Label(currency_frame, text="Valute Sottostanti (';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['underlying_currencies'] = ttk.Entry(currency_frame, width=40) # Nuovo campo per valute sottostanti
        self.fields['underlying_currencies'].pack(side=tk.LEFT, padx=(5, 20))

        # Tipo Dipendenza Sottostanti (Worst-of, etc.)
        dependency_frame = ttk.Frame(underlying_frame)
        dependency_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dependency_frame, text="Tipo Dipendenza Sottostanti:", width=35).pack(side=tk.LEFT)
        self.fields['underlying_dependency_type'] = ttk.Combobox(dependency_frame, width=25, state='readonly', # Larghezza aumentata
                                                               values=["",'Worst-Of', 'Best-Of', 'Average', 'Single', 'Basket Custom']) #aggiunta opzione vuota
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

        # NUOVO: Dividend Yields
        dividend_frame = ttk.Frame(underlying_frame)
        dividend_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dividend_frame, text="Dividend Yields (%; ';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['dividend_yields'] = ttk.Entry(dividend_frame, width=40)
        self.fields['dividend_yields'].pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(
            dividend_frame,
            text="(es: 2.5; 0.0; 3.1)", 
            font=('Arial', 8), foreground='gray'
        ).pack(side=tk.LEFT, padx=(5, 0))

        # =======================================
        # CARICA DATI ESISTENTI v15.1
        # =======================================
        
        self._load_existing_data_v15_1_corrected()
        
        # Focus su primo campo
        self.fields['isin'].focus()
        
        print("✅ Form completo v15.1 CORRECTED creato con successo")
    
    def _load_existing_data_v15_1_corrected(self):
        """
        Versione Corretta e Definitiva:
        - Carica i dati da un DIZIONARIO.
        - Applica i toggle dei campi (airbag, barriera dinamica) nell'ordine corretto
          per evitare di scrivere su widget disabilitati.

                """
        if not self.existing_data:
            print("📝 Popolamento form con valori di default per nuovo certificato.")
            # ... (la logica per i nuovi certificati qui rimane invariata) ...
            self.fields['issuer'].set('Vontobel')
            self.fields['certificate_type'].set('express')
            self.fields['issue_date'].insert(0, datetime.now().strftime('%Y-%m-%d'))
            self.fields['maturity_date'].insert(0, (datetime.now() + timedelta(days=3*365)).strftime('%Y-%m-%d'))
            self.fields['notional'].insert(0, '1000')
            self.fields['risk_free_rate'].insert(0, '3.50')
            self.fields['coupon_rate'].insert(0, '0.70')
            self.fields['coupon_frequency'].set('Mensile')
            self.fields['memory_feature'].set('True')
            self.fields['airbag_feature'].set('False')
            self.fields['coupon_barrier_type'].set('european')
            self.fields['capital_barrier_type'].set('protected')
            self.fields['currency'].set('EUR')
            self.fields['underlying_dependency_type'].set('Worst-Of')
            self.fields['dynamic_barrier_start_level'].insert(0, '100.00')
            self.fields['dynamic_barrier_end_level'].insert(0, '70.00')
            self.fields['step_down_rate'].insert(0, '5.0')
            self._toggle_airbag_level_field()
            self._on_capital_barrier_type_changed()
            self._update_dependency_description()
            return

        print("📊 === CARICAMENTO DATI DA DIZIONARIO (Logica Definitiva) ===")

        # Funzione helper per leggere da un DIZIONARIO in modo sicuro
        def get_value(key, default=None):
            val = self.existing_data.get(key, default)
            return val if val is not None else default

        # Funzione helper per popolare un widget
        def set_widget_value(field_name, value):
            if value is None:
                return
            try:
                widget = self.fields[field_name]
                if isinstance(widget, ttk.Combobox):
                    widget.set(str(value))
                elif isinstance(widget, tk.Text):
                    widget.delete('1.0', tk.END)
                    widget.insert('1.0', str(value))
                elif isinstance(widget, ttk.Entry):
                    widget.delete(0, tk.END)
                    widget.insert(0, str(value))
            except Exception as e:
                print(f"⚠️ Errore nel popolare il campo GUI '{field_name}' con valore '{value}': {e}")

        # --- CARICAMENTO DATI IN ORDINE LOGICO ---

        # 1. Carica TUTTI i campi semplici e quelli che controllano la UI
        #    (escludendo i campi dipendenti come 'airbag_level')
        simple_fields = [
            'isin', 'name', 'issuer', 'certificate_type', 'issue_date', 'maturity_date', 
            'notional', 'certificate_instrument_ticker', 'currency', 'coupon_frequency', 
            'memory_feature', 'underlying_dependency_type', 'coupon_barrier_type',
            'note_barriere', 'airbag_feature', 'capital_barrier_type' # I "controller"
        ]
        for field in simple_fields:
            set_widget_value(field, get_value(field))

        # 2. **LA TUA INTUIZIONE IN PRATICA**: Esegui i toggle SUBITO dopo aver impostato i controller
        self._toggle_airbag_level_field()
        self._on_capital_barrier_type_changed()
        self._update_dependency_description()

        # 3. Ora carica i campi rimanenti, inclusi quelli che erano disabilitati
        
        # Campi percentuali (convertiti da float 0.035 a stringa "3.50")
        percentage_fields = {
            'risk_free_rate': 2, 'coupon_rate': 3, 'coupon_barrier': 2, 'capital_barrier': 2, 
            'airbag_level': 2, 'dynamic_barrier_start_level': 2, 'step_down_rate': 3, 
            'dynamic_barrier_end_level': 2
        }
        for field, decimals in percentage_fields.items():
            val = get_value(field)
            if val is not None:
                # Se il campo è disabilitato (es. airbag_level), il set_widget_value non farà nulla, evitando errori.
                set_widget_value(field, f"{(val * 100):.{decimals}f}")

        # Campi lista (convertiti da lista a stringa separata da ';')
        list_fields = ['yahoo_ticker', 'underlying_names', 'underlying_currencies']
        for field in list_fields:
            val = get_value(field, [])
            set_widget_value(field, '; '.join(val))
        
        # Liste di numeri con formattazione speciale
        prezzi_val = get_value('prezzi_iniziali_sottostanti', [])
        if prezzi_val:
            price_strings = [f"{price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') for price in prezzi_val]
            set_widget_value('prezzi_iniziali_sottostanti', '; '.join(price_strings))

        dividends_val = get_value('dividend_yields', [])
        if dividends_val:
            yield_strings = [f"{(y * 100):.2f}" for y in dividends_val]
            set_widget_value('dividend_yields', '; '.join(yield_strings))

        # Campi rimanenti (note e interi)
        set_widget_value('airbag_notes', get_value('airbag_notes'))
        set_widget_value('observation_delay_months', get_value('observation_delay_months'))

        # Focus sul primo campo
        self.fields['isin'].focus()
        print("✅ Dati caricati correttamente con la nuova logica.") 
    
    def _save_v15_1_corrected(self):
        """
        Salvataggio v16 - Gestisce il separatore ';' per le liste e i numeri in formato EU.
        """
        print("💾 === INIZIO SALVATAGGIO v16 (Logica con ';') ===")
        
        result_data = {}
        raw_values = {field_name: widget.get("1.0", "end-1c") if isinstance(widget, tk.Text) else widget.get() for field_name, widget in self.fields.items()}

        required_fields = ['isin', 'name', 'issue_date', 'maturity_date', 'notional']
        for field in required_fields:
            if not raw_values.get(field):
                messagebox.showerror("Errore", f"Il campo '{field}' è obbligatorio.")
                return

        try:
            # Crea un dizionario pulito e convertito
            for field_name, value_str in raw_values.items():
                value = value_str.strip() if isinstance(value_str, str) else value_str
                if value == '' or (isinstance(value, str) and value.lower() == 'none'):
                    value = None

                # Campi a lista di stringhe (usano ';')
                if field_name in ['yahoo_ticker', 'underlying_names', 'underlying_currencies']:
                    result_data[field_name] = [item.strip() for item in value.split(';')] if value else []
                
                # CAMPO CHIAVE: Lista di numeri con formato EU
                elif field_name == 'prezzi_iniziali_sottostanti':
                    if not value:
                        result_data[field_name] = []
                    else:
                        prices = []
                        price_strings = value.split(';')
                        for p_str in price_strings:
                            if not p_str.strip(): continue
                            # Converte da formato EU (1.234,56) a float (1234.56)
                            clean_str = p_str.strip().replace('.', '').replace(',', '.')
                            prices.append(float(clean_str))
                        result_data[field_name] = prices

                # NUOVO: Lista di percentuali per i dividendi
                elif field_name == 'dividend_yields':
                    if not value:
                        result_data[field_name] = []
                    else:
                        yields = [float(y.strip().replace(',', '.')) / 100.0 for y in value.split(';')]
                        result_data[field_name] = yields
                 
                # Campi percentuali (formato anglosassone con '.')
                elif field_name in ['risk_free_rate', 'coupon_rate', 'coupon_barrier', 'capital_barrier', 'airbag_level', 'dynamic_barrier_start_level', 'step_down_rate', 'dynamic_barrier_end_level']:
                    result_data[field_name] = float(value.replace(',', '.')) / 100.0 if value is not None else None
                
                # Campi numerici semplici
                elif field_name == 'notional':
                    result_data[field_name] = float(value.replace(',', '.')) if value is not None else None
                elif field_name == 'observation_delay_months':
                    result_data[field_name] = int(value) if value is not None else None
                
                # Booleani e stringhe
                elif field_name in ['memory_feature', 'airbag_feature', 'dynamic_barrier_feature']:
                    result_data[field_name] = (str(value).lower() == 'true')
                else:
                    result_data[field_name] = value

        except (ValueError, TypeError) as e:
            messagebox.showerror("Errore di Input", f"Il valore '{value_str}' per il campo '{field_name}' non è valido.\nErrore: {e}")
            return

        # Imposta esplicitamente il flag della barriera dinamica
        # in base alla scelta fatta nel campo del tipo di barriera.
        if result_data.get('capital_barrier_type') == 'dynamic':
            result_data['dynamic_barrier_feature'] = True
        else:
            result_data['dynamic_barrier_feature'] = False

        #print("---- DEBUG DIALOG SALVA ----")
        #print(result_data)


        self.result = result_data
        self.dialog.destroy()
        print("💾 === SALVATAGGIO v16 COMPLETATO CON SUCCESSO ===")

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
            
            self.logger = logging.getLogger(__name__)

            # Definiamo PRIMA il percorso del file, così possiamo usarlo subito.
            self.cert_file = Path("src/app/data/certificates.json") # <-- SPOSTATA QUI

            # --- GESTIONE CENTRALIZZATA TRAMITE MANAGER ---
            print("▶️  Inizializzazione del Manager Enhanced come sorgente dati principale...")
            if ENHANCED_MANAGER_AVAILABLE:
                # Ora self.cert_file esiste e può essere usato qui.
                self.enhanced_manager = EnhancedCertificateManagerV15(config_dir=self.cert_file.parent)
                self.certificates = self.enhanced_manager.configurations # Lavoriamo su una reference
                print(f"✅ Enhanced Manager v15 inizializzato con {len(self.certificates)} certificati.")
            else:
                self.enhanced_manager = None
                self.certificates = self._load_certificates() # Fallback a caricamento locale
                print("⚠️  Enhanced Manager non disponibile. Gestione certificati locale.")

            # --- FINE GESTIONE CENTRALIZZATA ---

            # *** PORTFOLIO MANAGER INTEGRATION v15.1 ***
            try:
                from app.core.portfolio_manager import PortfolioManager, PortfolioGUIManager
                self.portfolio_manager = PortfolioManager(self.cert_file.parent)
                self.portfolio_gui = PortfolioGUIManager(self.portfolio_manager, self.root, self.certificates)
                print("✅ Portfolio Manager e GUI Manager inizializzati.")
            except ImportError as e:
                print(f"⚠️ Portfolio Manager non disponibile: {e}")
                self.portfolio_manager = None
                self.portfolio_gui = None   

            # Non c'è più bisogno di caricare i certificati qui, lo fa già il manager.
            
            # Setup GUI
            self._setup_gui_v15_1_corrected()
            
            # Refresh lista
            self._refresh_certificate_list()
            
            print("🚀 === GUI MANAGER v15.1 CORRECTED INIZIALIZZATO ===") 

    def get_selected_isin(self):
            """Restituisce l'ISIN del certificato selezionato nel treeview, o None se non c'è selezione."""
            selection = self.tree.selection()
            if selection:
                return self.tree.item(selection[0])['values'][0]
            return None

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
                  command=self._analyze_selected_certificate).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="📈 Esporta Analisi Excel", 
                  command=self._export_analysis_excel).pack(side=tk.LEFT, padx=(0, 5))
        
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
        system_buttons_frame.pack(side=tk.RIGHT)
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
        columns = ("ISIN", "Nome", "Tipo", "Emittente", "Risk-Free %", "Scadenza", "Stato")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "ISIN":
                self.tree.column(col, width=120)
            elif col == "Nome":
                self.tree.column(col, width=200)
            elif col == "Risk-Free %":
                self.tree.column(col, width=70)  # Ridotto
            elif col == "Scadenza":
                self.tree.column(col, width=90)  # Ridotto
            elif col == "Stato":
                self.tree.column(col, width=65)  # Ridotto
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
        """Calc Date che gestisce correttamente gli oggetti certificato."""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato per calcolare le date")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]
        
        # Prendiamo l'oggetto EnhancedCertificateConfig
        enhanced_config_obj = self.certificates.get(cert_id)
        if not enhanced_config_obj:
            messagebox.showerror("Errore", f"Certificato {cert_id} non trovato")
            return
        
        print(f"📅 === CALC DATE INTEGRATA per l'oggetto {cert_id} ===")
        
        try:
            if self.enhanced_manager:
                # Il Dialog di calcolo si aspetta un dizionario, non un oggetto.
                # Convertiamo il nostro base_config in un dizionario al volo.
                # NOTA: usiamo vars() per ottenere un dizionario dagli attributi di un oggetto.
                cert_data_as_dict = vars(copy.deepcopy(enhanced_config_obj.base_config))

                dialog = CalculoDateAutoDialogV15(
                    self.root, 
                    selected_certificate_id=cert_id,
                    configurations={cert_id: cert_data_as_dict}
                )
                
                self.root.wait_window(dialog.dialog)
                
                if hasattr(dialog, 'result') and dialog.result:
                    print(f"📅 Date calcolate per {cert_id}. Aggiornamento in corso...")
                    
                    # Aggiorniamo il nostro certificato esistente con i risultati
                    self.enhanced_manager.update_certificate_from_dict(cert_id, dialog.result)
                    
                    self._save_certificates()
                    self._refresh_certificate_list()
                    self._reselect_tree_item(cert_id)
                    messagebox.showinfo("Successo", f"Date calcolate e salvate per {cert_id}!")
                else:
                    print("📅 Calc date annullata dall'utente")
            else:
                messagebox.showerror("Errore", "Enhanced Manager non disponibile per calc date")
        except Exception as e:
            self.logger.error(f"Errore in _calculate_dates_integrated: {e}", exc_info=True)
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
                #self.certificates[cert_id] = cert_data #vecchio modo
                self.enhanced_manager.add_certificate_from_dict_v15(cert_id, cert_data) # NUOVO MODO
                
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
        """
        Modifica il certificato selezionato, accedendo correttamente ai dati
        dall'oggetto EnhancedCertificateConfig e usando il nome corretto del Dialog.
        """
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da modificare.")
            return

        selected_isin = self.tree.item(selection[0])['values'][0]

        # Recuperiamo l'intero oggetto EnhancedCertificateConfig
        cert_data_original_obj = self.certificates.get(selected_isin)
        if not cert_data_original_obj:
            messagebox.showerror("Errore", "Dati del certificato non trovati.")
            return

        # I dati per la GUI sono nel base_config dell'oggetto.
        # È un oggetto RealCertificateConfig, non un dizionario.
        cert_data_for_dialog = cert_data_original_obj.base_config

        print(f"✏️ === MODIFICA CERTIFICATO {selected_isin} v15.1 CORRECTED ===")
        original_rf = getattr(cert_data_for_dialog, 'risk_free_rate', 'N/A')
        print(f"📊 Risk-Free Rate originale: {original_rf}")

        try:
            cert_data_dict = self.enhanced_manager.get_certificate_data_for_gui(selected_isin)
            dialog = EnhancedCertificateDialogV15_1_Corrected(self.root, f"Modifica {selected_isin}", cert_data_dict)
            
            if hasattr(dialog, 'result') and dialog.result:
                updated_data = dialog.result
                cert_id = updated_data['isin'] # Il risultato del dialog è un dizionario

                # Deleghiamo l'aggiornamento al manager
                self.enhanced_manager.add_certificate_from_dict_v15(cert_id, updated_data)
                
                # Le operazioni di salvataggio e refresh sono gestite dal manager
                self._save_certificates()
                self._refresh_certificate_list()
                self._reselect_tree_item(cert_id)
                #self._display_certificate_details(cert_id)
                
                messagebox.showinfo("Successo", f"Certificato {cert_id} modificato con successo!")
                print(f"✅ Certificato {cert_id} modificato e salvato.")
            else:
                print(f"❌ Dialog di modifica annullato.")

        except Exception as e:
            self.logger.error(f"Errore durante la modifica di {selected_isin}: {e}", exc_info=True)
            messagebox.showerror("Errore Modifica", f"Si è verificato un errore imprevisto:\n{e}")
             
    def _refresh_certificate_list(self):
        """Refresh lista certificati accedendo correttamente agli attributi dell'oggetto."""
        
        # Pulisci tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Aggiungi certificati
        for cert_id, enhanced_config in self.certificates.items():
            if enhanced_config:
                # enhanced_config è un oggetto, accediamo al suo base_config per i dati
                cert_data = enhanced_config.base_config 
                
                # Usiamo getattr per accedere agli attributi in modo sicuro (come .get)
                risk_free_rate = getattr(cert_data, 'risk_free_rate', 0)
                
                if isinstance(risk_free_rate, (int, float)):
                    # La logica di formattazione rimane la stessa
                    rf_display = f"{risk_free_rate * 100:.2f}%" if risk_free_rate <= 1.0 else f"{risk_free_rate:.2f}%"
                else:
                    rf_display = str(risk_free_rate)
                
                status = getattr(enhanced_config, 'status', 'N/A')
                
                self.tree.insert("", tk.END, values=(
                    getattr(cert_data, 'isin', 'N/A'),
                    getattr(cert_data, 'name', 'N/A'),
                    getattr(cert_data, 'certificate_type', 'N/A'),
                    getattr(cert_data, 'issuer', 'N/A'),
                    rf_display,
                    getattr(cert_data, 'maturity_date', 'N/A'),
                    status
                ))
        
        # Status update
        count = len(self.certificates)
        self.status_var.set(f"Sistema Certificati v15.1 CORRECTED - {count} certificati caricati")

    def _reselect_tree_item(self, cert_id_to_select: str):
        """
        Scorre il treeview e riseleziona la riga corrispondente all'ISIN fornito.
        """
        for item_id in self.tree.get_children():
            item_values = self.tree.item(item_id, 'values')
            if item_values and item_values[0] == cert_id_to_select:
                self.tree.selection_set(item_id)
                self.tree.focus(item_id)
                self.tree.see(item_id) # Assicura che la riga sia visibile
                self._on_selection_changed() # Simula il click per aggiornare i dettagli
                break
            
    def _on_selection_changed(self, event=None):
        """Gestione selezione certificato"""
        selection = self.tree.selection()
        if selection:
            cert_id = self.tree.item(selection[0])['values'][0]
            self._display_certificate_details(cert_id)

    def _display_certificate_details(self, cert_id):
        """Visualizza dettagli accedendo correttamente agli attributi dell'oggetto e le date senza orario"""
        
        if cert_id not in self.certificates:
            return
        
        enhanced_config = self.certificates[cert_id]
        if enhanced_config is None:
            self.logger.warning(f"Nessun dato trovato per il certificato con ID: {cert_id}")
            self.details_text.delete(1.0, tk.END)
            return

        # Lavoriamo sempre con base_config per i dati principali
        cert_data = enhanced_config.base_config

        # Funzione helper per la formattazione
        def format_percentage(value, decimals=2):
            if isinstance(value, (int, float)):
                return f"{value * 100:.{decimals}f}%" if value <= 1.0 and value !=0 else f"{value:.{decimals}f}%"
            return str(value) if value is not None else 'N/A'

        # Funzione helper per l'accesso sicuro agli attributi
        def get_attr(obj, attr_name, default='N/A'):
            # Aggiungiamo un controllo per ritornare il default se il valore è None
            val = getattr(obj, attr_name, default)
            return val if val is not None else default
        
        # === MODIFICA FORMATO DATA ===
        issue_date_obj = get_attr(cert_data, 'issue_date')
        maturity_date_obj = get_attr(cert_data, 'maturity_date')
        
        issue_date_str = issue_date_obj.strftime('%Y-%m-%d') if isinstance(issue_date_obj, datetime) else issue_date_obj
        maturity_date_str = maturity_date_obj.strftime('%Y-%m-%d') if isinstance(maturity_date_obj, datetime) else maturity_date_obj
        # === FINE MODIFICA ===

        yahoo_tickers_data = get_attr(cert_data, 'yahoo_ticker', [])
        yahoo_tickers_display = ', '.join(yahoo_tickers_data) if isinstance(yahoo_tickers_data, list) else str(yahoo_tickers_data)

        rf_display = format_percentage(get_attr(cert_data, 'risk_free_rate', 0))

        airbag_feature = get_attr(cert_data, 'airbag_feature', False)
        airbag_level_str = format_percentage(get_attr(cert_data, 'airbag_level', 0)) if airbag_feature else "N/A"
        airbag_notes = get_attr(cert_data, 'airbag_notes', '') or ''
        
        prezzi_iniziali = get_attr(cert_data, 'prezzi_iniziali_sottostanti', 'N/A')
        note_barriere = get_attr(cert_data, 'note_barriere', '') or ''

        # (La funzione format_prezzi_iniziali interna può rimanere la stessa)
        def format_prezzi_iniziali(val):
            #... (la funzione interna rimane invariata)
            if not val or val == 'N/A': return 'N/A'
            try:
                parts = [x.strip() for x in str(val).split(',')]
                formatted = []
                for p in parts:
                    p_clean = p.replace('.', '').replace(' ', '').replace("'", "").replace(',', '.')
                    num = float(p_clean)
                    formatted.append(f"{num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                return ', '.join(formatted)
            except Exception: return val

        details = f"""DETTAGLI CERTIFICATO v16
{'='*60}

INFORMAZIONI BASE:
ISIN: {get_attr(cert_data, 'isin')}
Nome Certificato: {get_attr(cert_data, 'name')}
Ticker Strumento: {get_attr(cert_data, 'certificate_instrument_ticker')}
Tipo Certificato: {get_attr(cert_data, 'certificate_type')}
Emittente: {get_attr(cert_data, 'issuer')}
Stato: {get_attr(enhanced_config, 'status')}

DATE E PARAMETRI:
Data Emissione: {issue_date_str}
Data Scadenza: {maturity_date_str}
Nominale: €{get_attr(cert_data, 'notional', 0):,.2f}

TASSI:
Risk-Free Rate: {rf_display}
Tasso Cedola Periodico: {format_percentage(get_attr(cert_data, 'coupon_rate', 0), decimals=3)}
Frequenza Cedola: {get_attr(cert_data, 'coupon_frequency')}

CARATTERISTICHE:
Effetto Memoria: {get_attr(cert_data, 'memory_feature')}
Airbag: {airbag_feature}
Livello Airbag: {airbag_level_str}
"""
        if airbag_notes:
            details += f"Note Airbag: {airbag_notes}\n"

        details += f"""
BARRIERE:
Barriera Cedola: {format_percentage(get_attr(cert_data, 'coupon_barrier', 0))} ({get_attr(cert_data, 'coupon_barrier_type')})
Barriera Capitale: {format_percentage(get_attr(cert_data, 'capital_barrier', 0))} ({get_attr(cert_data, 'capital_barrier_type')})
"""
        if note_barriere:
            details += f"Note Barriere: {note_barriere}\n"

        details += f"""
BARRIERE DINAMICHE:
Abilitata: {get_attr(cert_data, 'dynamic_barrier_feature', False)}
"""
        if get_attr(cert_data, 'dynamic_barrier_feature', False):
            details += f"""Livello Iniziale: {format_percentage(get_attr(cert_data, 'dynamic_barrier_start_level', 0))}
Step Down Rate: {format_percentage(get_attr(cert_data, 'step_down_rate', 0), decimals=3)}
Livello Finale: {format_percentage(get_attr(cert_data, 'dynamic_barrier_end_level', 0))}
Mesi di Ritardo Osservazione: {get_attr(cert_data, 'observation_delay_months')}
"""

        details += f"""
SOTTOSTANTI:
Tickers Sottostanti (Yahoo): {yahoo_tickers_display}
Prezzi Iniziali/Strike: {format_prezzi_iniziali(prezzi_iniziali)}
Nomi/Desc Sottostanti: {get_attr(cert_data, 'underlying_names')}
Valute Sottostanti: {get_attr(cert_data, 'underlying_currencies')}
Tipo Dipendenza Sottostanti: {get_attr(cert_data, 'underlying_dependency_type')}
"""
        dependency_type = get_attr(cert_data, 'underlying_dependency_type')
        if dependency_type and dependency_type in self._dependency_descriptions:
            details += f"Descrizione Dipendenza: {self._dependency_descriptions[dependency_type]}\n"
        
        details += f"""
Valuta Certificato: {get_attr(cert_data, 'currency')}

DATI AVANZATI:
Date Cedole: {len(get_attr(cert_data, 'coupon_dates', []))} date
Autocall Levels: {len(get_attr(cert_data, 'autocall_levels', []))} livelli
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
            """
            Salva tutti i certificati DELEGANDO l'operazione al manager.
            Questo centralizza la logica di salvataggio, inclusa la creazione dei backup.
            """
            if self.enhanced_manager:
                try:
                    # La GUI non sa come si salva, chiede semplicemente al manager di farlo.
                    # Sarà il manager ad occuparsi del file, del formato e del backup.
                    self.enhanced_manager.save_all_certificates()
                    self.status_var.set(f"Salvataggio completato con successo tramite manager.")
                    print("✅ Salvataggio delegato al manager completato.")
                    return True
                except Exception as e:
                    self.logger.error(f"Errore durante il salvataggio delegato al manager: {e}", exc_info=True)
                    messagebox.showerror("Errore Salvataggio", f"Il manager ha riscontrato un errore durante il salvataggio:\n{e}")
                    return False
            else:
                # Questa sezione è un "fallback" nel caso in cui il manager non fosse disponibile.
                # Mantiene la vecchia logica di salvataggio diretto per robustezza.
                print("⚠️  Manager non disponibile, si procede con il salvataggio locale (legacy).")
                try:
                    # La logica di backup e salvataggio che prima era qui, rimane per il fallback.
                    if self.cert_file.exists():
                        backup_file = self.cert_file.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                        import shutil
                        shutil.copy2(self.cert_file, backup_file)
                        print(f"💾 Backup locale (fallback) creato: {backup_file}")

                    with open(self.cert_file, 'w', encoding='utf-8') as f:
                        json.dump(self.certificates, f, ensure_ascii=False, indent=2, default=str)

                    self.status_var.set(f"Salvataggio locale (fallback) completato.")
                    print(f"✅ Certificati salvati localmente in {self.cert_file}")
                    return True

                except Exception as e:
                    self.logger.error(f"Errore durante il salvataggio locale (fallback): {e}", exc_info=True)
                    messagebox.showerror("Errore Salvataggio Locale", f"Errore durante il salvataggio dei certificati:\n{e}")
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
            # del self.certificates[cert_id] #vecchio modo
            if self.enhanced_manager.delete_certificate(cert_id): # NUOVO MODO
                self._refresh_certificate_list()

            if self._save_certificates():
                self._refresh_certificate_list()
                self.details_text.delete(1.0, tk.END)
                messagebox.showinfo("Eliminato", f"Certificato {cert_id} eliminato")
    
    def _analyze_selected_certificate(self):
        """
        *** VERSIONE COMPLETAMENTE RIVISTA E FUNZIONANTE ***
        Esegue l'analisi completa:
        1. Controlla la presenza dei dati necessari (date cedole).
        2. Recupera i dati di mercato aggiornati.
        3. Esegue l'analisi di rischio (VaR, Vol, etc.).
        4. Esegue il calcolo del Fair Value.
        5. Mostra un riepilogo completo dei risultati.
        """

        selected_isin = self.get_selected_isin()
        if not selected_isin:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da analizzare.")
            return
        
        # >>> INIZIO NUOVO BLOCCO DI VALIDAZIONE <<<
        cert_obj = self.enhanced_manager.configurations.get(selected_isin)
        if not cert_obj or not cert_obj.base_config:
            messagebox.showerror("Errore Interno", f"Impossibile recuperare i dati per il certificato {selected_isin}.")
            return

        base_conf = cert_obj.base_config
        # Usiamo getattr per sicurezza, nel caso gli attributi non esistessero
        num_underlyings = len(getattr(base_conf, 'underlying_assets', []))
        num_initial_prices = len(getattr(base_conf, 'prezzi_iniziali_sottostanti', []))

        if num_initial_prices == 0:
            messagebox.showwarning("Dati Obbligatori Mancanti",
                                "Il campo 'Prezzi Iniziali/Strike' è obbligatorio per l'analisi.\n\n"
                                "Per favore, modifica il certificato e inserisci i valori corretti prima di procedere.")
            return

        if num_underlyings != num_initial_prices:
            messagebox.showwarning("Dati Incoerenti",
                                f"Il numero di sottostanti ({num_underlyings}) non corrisponde al numero di prezzi iniziali ({num_initial_prices}).\n\n"
                                "Per favore, controlla i dati del certificato.")
            return
    
        if not self.enhanced_manager:
            messagebox.showerror("Errore", "Funzionalità di analisi non disponibile. Enhanced Manager non trovato.")
            return

       # --- MODIFICA 1: CONTROLLO PREVENTIVO SULLE DATE CEDOLA ---
        try:
            cert_data_dict = self.enhanced_manager.get_certificate_data_for_gui(selected_isin)
            if not cert_data_dict.get('coupon_dates'):
                messagebox.showwarning(
                    "Dati Mancanti",
                    f"Il certificato '{selected_isin}' non ha una schedulazione delle cedole.\n\n"
                    "Per favore, usa il pulsante 'Calc Date' per generarle prima di avviare l'analisi."
                )
                return
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile verificare i dati del certificato: {e}")
            return
        # --- FINE MODIFICA 1 ---

        self.status_var.set(f"Analisi in corso per {selected_isin}... (Recupero dati di mercato)")
        self.root.update_idletasks()

        try:
            # 1. DELEGA AL MANAGER: chiede di aggiornare i dati e restituire la config
            config_pronta_per_analisi = self.enhanced_manager.refresh_and_get_certificate_for_analysis(selected_isin)

            if not config_pronta_per_analisi:
                messagebox.showerror("Errore", f"Impossibile preparare il certificato {selected_isin} per l'analisi.")
                self.status_var.set("Analisi fallita.")
                return

            # 2. Converti la configurazione aggiornata in un oggetto certificato "vivo"
            importer = RealCertificateImporter()
            certificate_object = importer.import_certificate(config_pronta_per_analisi)

            # 3. Esegui l'analisi di rischio
            analyzer = UnifiedRiskAnalyzer()
            risk_metrics = analyzer.analyze_certificate_risk(certificate_object, n_simulations=1000)
            self.logger.info(f"Analisi di rischio completata. VaR 95%: {risk_metrics.var_95:.2%}")

            # --- MODIFICA 2: CALCOLO DEL FAIR VALUE ---
            self.logger.info("💰 Calcolo del Fair Value in corso...")
            fair_value_results = {}
            try:
                fv_analyzer = UnifiedCertificateAnalyzer(certificate_object)
                fair_value_results = fv_analyzer.calculate_fair_value(n_simulations=5000)
                self.logger.info(f"✅ Fair Value calcolato: {fair_value_results.get('fair_value'):.2f}")
            except Exception as fv_error:
                self.logger.error(f"⚠️ Errore nel calcolo del Fair Value: {fv_error}", exc_info=True)
                fair_value_results = {'fair_value': 0, 'error': str(fv_error)}
            # --- FINE MODIFICA 2 ---

            self.logger.info(f"RISULTATI ANALISI per {selected_isin}: FV={fair_value_results.get('fair_value', 'N/A'):.2f}, VaR 95%={risk_metrics.var_95:.2%}, Volatilità={risk_metrics.volatility:.2%}") #Volatilità



            # --- MODIFICA 3: VISUALIZZAZIONE COMPLETA DEI RISULTATI ---
            # Prepara il messaggio formattato
            fair_value = fair_value_results.get('fair_value', 'N/A')
            exp_return = fair_value_results.get('expected_return', 'N/A')

            # Recuperiamo l'intero oggetto aggiornato dal manager per accedere ai dati di mercato
            enhanced_config_aggiornato = self.enhanced_manager.configurations[selected_isin]
            market_data = enhanced_config_aggiornato.in_life_state.current_market_data
            market_price = market_data.get('certificate_market_price', 'N/A')

            """"
            # 4. Mostra i risultati (questa funzione andrà creata o migliorata)
            # self.update_analysis_results_display(risk_metrics.to_dict())
            messagebox.showinfo("Analisi Completata",
                                f"Analisi per {selected_isin} completata con successo.\n\n"
                                f"VaR 95%: {risk_metrics.var_95:.2%}\n"
                                f"VaR 99%: {risk_metrics.var_99:.2%}\n"
                                f"Volatilità: {risk_metrics.volatility:.2%}\n"
                                f"Sharpe Ratio: {risk_metrics.sharpe_ratio:.3f}")

            """
            # Formattazione sicura dei valori
            mkt_price_str = f"€ {market_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if isinstance(market_price, (int, float)) else "N/A"
            fv_str = f"€ {fair_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if isinstance(fair_value, (int, float)) else "N/A"
            ret_str = f"{exp_return:.2%}".replace(".", ",") if isinstance(exp_return, (int, float)) else "N/A"
            var95_str = f"{risk_metrics.var_95:.2%}".replace(".", ",")
            vol_str = f"{risk_metrics.volatility:.2%}".replace(".", ",")

            summary_message = f"""
ANALISI COMPLETA - {selected_isin}
{'='*50}

VALUTAZIONE:
  • Prezzo di Mercato: {mkt_price_str}
  • Fair Value Stimato: {fv_str}
  • Rendimento Atteso: {ret_str}

PRINCIPALI METRICHE DI RISCHIO:
  • VaR 95% (Max Perdita attesa): {var95_str}
  • Volatilità Annualizzata: {vol_str}
  • Sharpe Ratio: {risk_metrics.sharpe_ratio:.3f}

{'='*50}
Analisi basata su {1000} simulazioni di rischio e {5000} per il fair value.
"""

            #messagebox.showinfo("Analisi Completata", summary_message)
            from app.core.enhanced_certificate_manager_fixed import PreviewDialog 
            PreviewDialog(self.root, f"Analisi Completa - {selected_isin}", summary_message)


            self.status_var.set("Analisi completata con successo.")



        except Exception as e:
            self.logger.error(f"Errore durante l'analisi del certificato {selected_isin}: {e}", exc_info=True)
            messagebox.showerror("Errore di Analisi", f"Si è verificato un errore durante l'analisi:\n{e}")
            self.status_var.set("Analisi fallita.")

    def _export_analysis_excel(self):
        """Esporta analisi avanzata in Excel (versione corretta)."""
        selected_isin = self.get_selected_isin()
        if not selected_isin:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da esportare")
            return
        
        cert_data = self.certificates.get(selected_isin)
        if not cert_data:
            messagebox.showerror("Errore", f"Dati per il certificato {selected_isin} non trovati.")
            return

        self.status_var.set(f"Esportazione Excel per {selected_isin} in corso...")
        self.root.update_idletasks()

        try:
            # Stessa logica della funzione di analisi
            config = RealCertificateConfig(**cert_data)
            importer = RealCertificateImporter()
            certificate_object = importer.import_certificate(config)
            analyzer = UnifiedRiskAnalyzer()
            risk_metrics = analyzer.analyze_certificate_risk(certificate_object)
            analysis_results = {
                'risk_metrics': risk_metrics.to_dict(),
                'fair_value': {} # Placeholder
            }
            
            exporter = EnhancedExcelExporter() # Assicurati che sia importato da real_certificate_integration
            report_path = exporter.create_comprehensive_certificate_report(certificate_object, analysis_results)

            if report_path:
                messagebox.showinfo("Export Completato", f"Report Excel creato:\n{report_path}")
            else:
                messagebox.showerror("Errore Export", "Creazione del report fallita.")

        except Exception as e:
            self.logger.error(f"Errore durante l'export Excel per {selected_isin}: {e}", exc_info=True)
            messagebox.showerror("Errore Durante l'Export", f"Si è verificato un errore:\n{e}")
        finally:
            self.status_var.set("Pronto")    

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
        messagebox.showerror("Errore Sistema", 
            f"Errore critico avvio Sistema v15.1 CORRECTED:\n{e}\n\nContattare supporto tecnico")