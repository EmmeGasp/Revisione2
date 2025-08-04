# ==========================================================
# NOME FILE: main_window.py
# ULTIMA MODIFICA: 2025-08-03 (Logica Analisi Standard/What-If)
# VERSIONE: 1.9
# ==========================================================
#
# DESCRIZIONE:
# Modulo principale per la gestione grafica (Tkinter) dei certificati finanziari.
#
# CHANGELOG v1.9:
# - REFACTOR (Logica Analisi): Il pulsante "Analizza" ora distingue tra:
#   - Analisi Standard: Se i parametri non vengono modificati, i risultati vengono salvati permanentemente.
#   - Analisi What-If: Se i parametri vengono modificati, i risultati sono temporanei per la sessione.
# - REFACTOR (UI): La vista dettagliata è stata riorganizzata per mostrare in modo chiaro
#   l'analisi di base salvata e, separatamente, l'eventuale analisi what-if temporanea.
# - FIX: Il dialog di override ora rileva correttamente se i parametri sono stati modificati dall'utente.
#
# PRINCIPALI CLASSI/FUNZIONI:
# - EnhancedCertificateDialogV15_1_Corrected: Dialog avanzato per inserimento/modifica certificato
# - ParameterOverrideDialog: Dialog per l'override dei parametri, ora con logica di rilevamento modifiche.
# - SimpleCertificateGUIManagerV15_1_Corrected: Gestione GUI principale e interazione utente
# ==========================================================

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
import math
import textwrap # Per formattare la descrizione della dipendenza
from app.core.consolidated_risk_system import UnifiedRiskAnalyzer
from app.core.real_certificate_integration import RealCertificateImporter
from dateutil.relativedelta import relativedelta
from app.core.enhanced_certificate_manager_fixed import PreviewDialog
from app.core.unified_certificates import UnifiedCertificateAnalyzer, ExpressCertificate, PhoenixCertificate


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
            CalculoDateAutoDialogV15
        )
        from app.utils.date_utils import DateCalculationUtils

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

    def __init__(self, parent, title, enhanced_manager, existing_data=None):
        self.result = None
        self.enhanced_manager = enhanced_manager
        # Deepcopy funziona anche sugli oggetti
        self.existing_data = copy.deepcopy(existing_data) if existing_data else None
        self.dialog_closed = False

        print(f"📝 === APERTURA DIALOG v15.1 CORRECTED ===")
        print(f"📝 Title: {title}")

        if self.existing_data:
            if hasattr(self.existing_data, 'isin'):
                print(f"📝 Dati esistenti per l'oggetto con ISIN: {self.existing_data.get('isin')}")
            else:
                print(f"📝 Dati esistenti (dict): {list(self.existing_data.keys())}")
        else:
            print(f"📝 Nuovo certificato (form vuoto)")

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

    def _generate_temp_coupon_dates(self, data: dict) -> list | None:
        """
        Genera una lista di date cedola temporanee basandosi sui dati del form,
        per abilitare un controllo di coerenza autonomo.
        Restituisce None se i dati di input non sono validi.
        """
        frequency_map = {
            'Mensile': 1, 'Bimestrale': 2, 'Trimestrale': 3,
            'Quadrimestrale': 4, 'Semestrale': 6, 'Annuale': 12
        }
        try:
            start_str = data.get('issue_date')
            end_str = data.get('maturity_date')
            frequency_str = data.get('coupon_frequency')

            if not all([start_str, end_str, frequency_str]):
                return []

            start_date = datetime.strptime(start_str.split('T')[0], '%Y-%m-%d')
            end_date = datetime.strptime(end_str.split('T')[0], '%Y-%m-%d')

            months_step = frequency_map[frequency_str]

            dates = []
            current_date = start_date + relativedelta(months=months_step)
            while current_date <= end_date:
                dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += relativedelta(months=months_step)

            if not dates or dates[-1] != end_date.strftime('%Y-%m-%d'):
                 dates.append(end_date.strftime('%Y-%m-%d'))

            return dates
        except (ValueError, TypeError, KeyError) as e:
            print(f"❌ Impossibile generare date temporanee: {e}")
            messagebox.showwarning(
                "Dati Insufficienti per Controllo",
                f"Impossibile eseguire il controllo di coerenza sulla barriera.\n\n"
                f"Verifica la correttezza dei campi:\n"
                f" - Data Emissione\n"
                f" - Scadenza\n"
                f" - Frequenza\n\nErrore: {e}"
            )
            return None


    def _on_dialog_close(self):
        """Gestione chiusura dialog"""
        print("❌ Dialog v15.1 CORRECTED chiuso senza salvare")
        self.result = None
        self.dialog_closed = True
        self.dialog.destroy()

    def _setup_form_complete_v15_1_corrected(self):
        """Setup form completo v15.1 CORRECTED con TUTTI i campi"""

        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(main_container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(main_container, orient="horizontal", command=canvas.xview)

        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        fixed_bottom_frame = ttk.Frame(main_container)
        fixed_bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Separator(fixed_bottom_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 10))

        button_frame = ttk.Frame(fixed_bottom_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="❌ Annulla",
                  command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="💾 Salva Certificato v15.1",
                  command=self._save_v15_1_corrected).pack(side=tk.RIGHT)

        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)

        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)

        self._create_complete_form_fields_v15_1_corrected()

    def _create_complete_form_fields_v15_1_corrected(self):
        """*** FORM COMPLETO v15.1 CORRECTED *** - TUTTI i campi necessari"""

        self.fields = {}

        print("🏗️ === CREAZIONE FORM COMPLETO v15.1 CORRECTED ===")

        base_frame = ttk.LabelFrame(self.scrollable_frame, text="📋 Informazioni Base", padding=15)
        base_frame.pack(fill='x', padx=10, pady=5)

        row1_frame = ttk.Frame(base_frame)
        row1_frame.pack(fill=tk.X, pady=5)

        ttk.Label(row1_frame, text="ISIN:", width=15).pack(side=tk.LEFT)
        self.fields['isin'] = ttk.Entry(row1_frame, width=20, font=('Arial', 10, 'bold'))
        self.fields['isin'].pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(row1_frame, text="Nome:", width=15).pack(side=tk.LEFT)
        self.fields['name'] = ttk.Entry(row1_frame, width=30)
        self.fields['name'].pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(row1_frame, text="Ticker Strumento:", width=15).pack(side=tk.LEFT, padx=(20,0))
        self.fields['certificate_instrument_ticker'] = ttk.Entry(row1_frame, width=15)
        self.fields['certificate_instrument_ticker'].pack(side=tk.LEFT, padx=(5,0))

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

        ttk.Label(row2_frame, text="Tipo:", width=15).pack(side=tk.LEFT)
        self.fields['certificate_type'] = ttk.Combobox(
            row2_frame, width=18,
            values=[
                'express', 'cash_collect', 'phoenix', 'barrier_reverse_convertible', 'digitale'
            ]
        )
        self.fields['certificate_type'].pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(
            row2_frame,
            text="(Usa classificazione ACEPI se possibile)",
            font=('Arial', 8, 'italic'),
            foreground='gray'
        ).pack(side=tk.LEFT, padx=(10, 0))

        row3_frame = ttk.Frame(base_frame)
        row3_frame.pack(fill=tk.X, pady=5)

        ttk.Label(row3_frame, text="Data Emissione:", width=15).pack(side=tk.LEFT)
        self.fields['issue_date'] = ttk.Entry(row3_frame, width=12)
        self.fields['issue_date'].pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(row3_frame, text="(AAAA-MM-DD)", font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(2, 20))

        ttk.Label(row3_frame, text="Scadenza:", width=15).pack(side=tk.LEFT)
        self.fields['maturity_date'] = ttk.Entry(row3_frame, width=12)
        self.fields['maturity_date'].pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(row3_frame, text="(AAAA-MM-DD)", font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(2, 0))

        financial_frame = ttk.LabelFrame(self.scrollable_frame, text="💰 Parametri Finanziari", padding=15)
        financial_frame.pack(fill='x', padx=10, pady=5)

        fin_row1_frame = ttk.Frame(financial_frame)
        fin_row1_frame.pack(fill=tk.X, pady=5)

        ttk.Label(fin_row1_frame, text="Nominale:", width=15).pack(side=tk.LEFT)
        self.fields['notional'] = ttk.Entry(fin_row1_frame, width=15)
        self.fields['notional'].pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(fin_row1_frame, text="Risk-Free Rate (%):", width=18).pack(side=tk.LEFT)
        self.fields['risk_free_rate'] = ttk.Entry(fin_row1_frame, width=10)
        self.fields['risk_free_rate'].pack(side=tk.LEFT, padx=(5, 5))

        ttk.Label(fin_row1_frame, text="(es: 3.5 per 3.5%, usa '.' come decimale, valore su base annuale)",
                 font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(5, 0))

        fin_row2_frame = ttk.Frame(financial_frame)
        fin_row2_frame.pack(fill=tk.X, pady=5)

        ttk.Label(fin_row2_frame, text="Tasso Cedola (% del periodo):", width=25).pack(side=tk.LEFT)
        self.fields['coupon_rate'] = ttk.Entry(fin_row2_frame, width=10)
        self.fields['coupon_rate'].pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(fin_row2_frame, text="(es. 0.7)", font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=(2, 20))

        ttk.Label(fin_row2_frame, text="Frequenza:", width=15).pack(side=tk.LEFT)
        self.fields['coupon_frequency'] = ttk.Combobox(fin_row2_frame, width=12, state='readonly',
                                                     values=['Mensile', 'Bimestrale', 'Trimestrale', 'Quadrimestrale', 'Semestrale', 'Annuale'])
        self.fields['coupon_frequency'].pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(fin_row2_frame, text="Valuta Certificato:", width=18).pack(side=tk.LEFT, padx=(20,0))
        self.fields['currency'] = ttk.Combobox(fin_row2_frame, width=8, state='readonly',
                                             values=['EUR', 'USD', 'GBP', 'CHF', 'JPY'])
        self.fields['currency'].pack(side=tk.LEFT, padx=(5, 0))

        features_frame = ttk.LabelFrame(self.scrollable_frame, text="🛡️ Caratteristiche Prodotto", padding=15)
        features_frame.pack(fill='x', padx=10, pady=5)

        memory_frame = ttk.Frame(features_frame)
        memory_frame.pack(fill=tk.X, pady=5)

        ttk.Label(memory_frame, text="Effetto Memoria:", width=15).pack(side=tk.LEFT)
        self.fields['memory_feature'] = ttk.Combobox(memory_frame, width=12,
                                                   values=['True', 'False'])
        self.fields['memory_feature'].pack(side=tk.LEFT, padx=(5, 20))

        airbag_control_frame = ttk.Frame(features_frame)
        airbag_control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(airbag_control_frame, text="Airbag:", width=15).pack(side=tk.LEFT)
        self.fields['airbag_feature'] = ttk.Combobox(airbag_control_frame, width=12,
                                                   values=['True', 'False'])
        self.fields['airbag_feature'].pack(side=tk.LEFT, padx=(5, 20))
        self.fields['airbag_feature'].bind(
            "<<ComboboxSelected>>",
            lambda event: self._toggle_airbag_level_field(event, clear_on_disable=True)
        )

        self.airbag_level_label = ttk.Label(airbag_control_frame, text="Livello Airbag (%):", width=15)
        self.airbag_level_label.pack(side=tk.LEFT)
        self.fields['airbag_level'] = ttk.Entry(airbag_control_frame, width=10)
        self.fields['airbag_level'].pack(side=tk.LEFT, padx=(5, 0))

        self.airbag_notes_label = ttk.Label(airbag_control_frame, text="Note Airbag:", width=12)
        self.airbag_notes_label.pack(side=tk.LEFT, padx=(20, 0))
        self.fields['airbag_notes'] = tk.Text(airbag_control_frame, width=30, height=2, wrap=tk.WORD)
        self.fields['airbag_notes'].pack(side=tk.LEFT, padx=(5, 0))

        self._toggle_airbag_level_field()

        barriers_frame = ttk.LabelFrame(self.scrollable_frame, text="🚧 Livelli Barriera (valori %)", padding=15)
        barriers_frame.pack(fill='x', padx=10, pady=5)

        barrier_row1_frame = ttk.Frame(barriers_frame)
        barrier_row1_frame.pack(fill=tk.X, pady=5)

        ttk.Label(barrier_row1_frame, text="Barriera Cedola (%):", width=18).pack(side=tk.LEFT)
        self.fields['coupon_barrier'] = ttk.Entry(barrier_row1_frame, width=10)
        self.fields['coupon_barrier'].pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(barrier_row1_frame, text="Tipo:", width=8).pack(side=tk.LEFT)
        self.fields['coupon_barrier_type'] = ttk.Combobox(barrier_row1_frame, width=12, state='readonly',
                                                        values=['none', 'european', 'american'])
        self.fields['coupon_barrier_type'].pack(side=tk.LEFT, padx=(5, 0))

        barrier_row2_frame = ttk.Frame(barriers_frame)
        barrier_row2_frame.pack(fill=tk.X, pady=5)

        ttk.Label(barrier_row2_frame, text="Barriera Capitale (%):", width=18).pack(side=tk.LEFT)
        self.fields['capital_barrier'] = ttk.Entry(barrier_row2_frame, width=10)
        self.fields['capital_barrier'].pack(side=tk.LEFT, padx=(5, 20))


        ttk.Label(barrier_row2_frame, text="Tipo:", width=8).pack(side=tk.LEFT)
        self.fields['capital_barrier_type'] = ttk.Combobox(barrier_row2_frame, width=12, state='readonly',
                                                         values=['protected', 'none', 'dynamic'])
        self.fields['capital_barrier_type'].pack(side=tk.LEFT, padx=(5, 0))
        self.fields['capital_barrier_type'].bind("<<ComboboxSelected>>", self._on_capital_barrier_type_changed)

        self.dynamic_barrier_params_frame = ttk.LabelFrame(barriers_frame, text="⚙️ Parametri Barriera Dinamica", padding=15)

        db_row1_frame = ttk.Frame(self.dynamic_barrier_params_frame)
        db_row1_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_row1_frame, text="Livello Iniziale (%):", width=25).pack(side=tk.LEFT)
        self.fields['dynamic_barrier_start_level'] = ttk.Entry(db_row1_frame, width=10)
        self.fields['dynamic_barrier_start_level'].pack(side=tk.LEFT, padx=(5, 20))

        db_row2_frame = ttk.Frame(self.dynamic_barrier_params_frame)
        db_row2_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_row2_frame, text="Step Down Rate (%):", width=25).pack(side=tk.LEFT)
        self.fields['step_down_rate'] = ttk.Entry(db_row2_frame, width=10)
        self.fields['step_down_rate'].pack(side=tk.LEFT, padx=(5, 20))

        db_row3_frame = ttk.Frame(self.dynamic_barrier_params_frame)
        db_row3_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_row3_frame, text="Livello Finale (%):", width=25).pack(side=tk.LEFT)
        self.fields['dynamic_barrier_end_level'] = ttk.Entry(db_row3_frame, width=10)
        self.fields['dynamic_barrier_end_level'].pack(side=tk.LEFT, padx=(5, 0))

        db_row4_frame = ttk.Frame(self.dynamic_barrier_params_frame)
        db_row4_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_row4_frame, text="Mesi di Ritardo Osservazione:", width=25).pack(side=tk.LEFT)
        self.fields['observation_delay_months'] = ttk.Entry(db_row4_frame, width=10)
        self.fields['observation_delay_months'].pack(side=tk.LEFT, padx=(5, 0))

        note_barriere_frame = ttk.Frame(barriers_frame)
        note_barriere_frame.pack(fill=tk.X, pady=5)
        ttk.Label(note_barriere_frame, text="Note Barriere:", width=15).pack(side=tk.LEFT)
        self.fields['note_barriere'] = tk.Text(note_barriere_frame, width=60, height=2, wrap=tk.WORD)
        self.fields['note_barriere'].pack(side=tk.LEFT, padx=(5, 0))

        underlying_frame = ttk.LabelFrame(self.scrollable_frame, text="📈 Sottostanti", padding=15)
        underlying_frame.pack(fill='x', padx=10, pady=5)

        ticker_frame = ttk.Frame(underlying_frame)
        ticker_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ticker_frame, text="Tickers Sottostanti (Yahoo, ';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['yahoo_ticker'] = ttk.Entry(ticker_frame, width=40)
        self.fields['yahoo_ticker'].pack(side=tk.LEFT, padx=(5, 20))

        strike_frame = ttk.Frame(underlying_frame)
        strike_frame.pack(fill=tk.X, pady=5)
        ttk.Label(strike_frame, text="Prezzi Iniziali/Strike (';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['prezzi_iniziali_sottostanti'] = ttk.Entry(strike_frame, width=40)
        self.fields['prezzi_iniziali_sottostanti'].pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(
            strike_frame,
            text="(Formato EU:1.234,56; 57,12)",
            font=('Arial', 8), foreground='gray'
        ).pack(side=tk.LEFT, padx=(5, 0))

        desc_frame = ttk.Frame(underlying_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="Nomi/Desc Sottostanti (';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['underlying_names'] = ttk.Entry(desc_frame, width=60)
        self.fields['underlying_names'].pack(side=tk.LEFT, padx=(5,0))

        currency_frame = ttk.Frame(underlying_frame)
        currency_frame.pack(fill=tk.X, pady=5)

        ttk.Label(currency_frame, text="Valute Sottostanti (';' sep.):", width=35).pack(side=tk.LEFT)
        self.fields['underlying_currencies'] = ttk.Entry(currency_frame, width=40)
        self.fields['underlying_currencies'].pack(side=tk.LEFT, padx=(5, 20))

        dependency_frame = ttk.Frame(underlying_frame)
        dependency_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dependency_frame, text="Tipo Dipendenza Sottostanti:", width=35).pack(side=tk.LEFT)
        self.fields['underlying_dependency_type'] = ttk.Combobox(dependency_frame, width=25, state='readonly',
                                                               values=["",'Worst-Of', 'Best-Of', 'Average', 'Single', 'Basket Custom'])
        self.fields['underlying_dependency_type'].pack(side=tk.LEFT, padx=(5,0))
        self.fields['underlying_dependency_type'].bind("<<ComboboxSelected>>", self._update_dependency_description)

        self.dependency_description_label = ttk.Label(underlying_frame, text="",
                                                     font=("Arial", 9, "italic"),
                                                     foreground="gray",
                                                     wraplength=700)
        self.dependency_description_label.pack(fill=tk.X, padx=10, pady=(0, 5))
        self._update_dependency_description()

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

        self._load_existing_data_v15_1_corrected()

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
            self.fields['step_down_rate'].insert(0, '1.0')
            self._toggle_airbag_level_field()
            self._on_capital_barrier_type_changed()
            self._update_dependency_description()
            return

        print("📊 === CARICAMENTO DATI DA DIZIONARIO (Logica Definitiva) ===")

        def get_value(key, default=None):
            val = self.existing_data.get(key, default)
            return val if val is not None else default

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

        simple_fields = [
            'isin', 'name', 'issuer', 'certificate_type', 'issue_date', 'maturity_date',
            'notional', 'certificate_instrument_ticker', 'currency', 'coupon_frequency',
            'memory_feature', 'underlying_dependency_type', 'coupon_barrier_type',
            'note_barriere', 'airbag_feature', 'capital_barrier_type'
        ]
        for field in simple_fields:
            set_widget_value(field, get_value(field))

        self._toggle_airbag_level_field()
        self._on_capital_barrier_type_changed()
        self._update_dependency_description()

        percentage_fields = {
            'risk_free_rate': 2, 'coupon_rate': 3, 'coupon_barrier': 2, 'capital_barrier': 2,
            'airbag_level': 2, 'dynamic_barrier_start_level': 2, 'step_down_rate': 3,
            'dynamic_barrier_end_level': 2
        }
        for field, decimals in percentage_fields.items():
            val = get_value(field)
            if val is not None:
                set_widget_value(field, f"{(val * 100):.{decimals}f}")

        list_fields = ['yahoo_ticker', 'underlying_names', 'underlying_currencies']
        for field in list_fields:
            val = get_value(field, [])
            set_widget_value(field, '; '.join(val))

        prezzi_val = get_value('prezzi_iniziali_sottostanti', [])
        if prezzi_val:
            price_strings = [f"{price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') for price in prezzi_val]
            set_widget_value('prezzi_iniziali_sottostanti', '; '.join(price_strings))

        dividends_val = get_value('dividend_yields', [])
        if dividends_val:
            yield_strings = [f"{(y * 100):.2f}" for y in dividends_val]
            set_widget_value('dividend_yields', '; '.join(yield_strings))

        set_widget_value('airbag_notes', get_value('airbag_notes'))
        set_widget_value('observation_delay_months', get_value('observation_delay_months'))

        self.fields['isin'].focus()
        print("✅ Dati caricati correttamente con la nuova logica.")

    def _calculate_expected_end_barrier(self, data: dict, temp_coupon_dates: list) -> float | None:
        """
        Calcola il livello finale atteso della barriera per il controllo di coerenza,
        utilizzando una lista di date calcolata al volo.
        """
        try:
            coupon_dates = temp_coupon_dates
            issue_date = datetime.strptime(data['issue_date'].split('T')[0], '%Y-%m-%d')
            delay_months = data.get('observation_delay_months', 0) or 0
            start_level = data.get('dynamic_barrier_start_level')
            step_rate = data.get('step_down_rate')

            if start_level is None or step_rate is None:
                 print("⚠️ Controllo barriera saltato: livello iniziale o step rate non forniti.")
                 return None

            first_obs_date = issue_date + relativedelta(months=delay_months)

            num_steps = sum(1 for d_str in coupon_dates if datetime.strptime(d_str, '%Y-%m-%d') > first_obs_date)

            expected_level = start_level - (num_steps * step_rate)
            return expected_level

        except Exception as e:
            print(f"⚠️ Errore nel calcolo della barriera finale attesa: {e}")
            messagebox.showerror("Errore Calcolo Barriera", f"Si è verificato un errore nel calcolo della coerenza:\n{e}")
            return None

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
            for field_name, value_str in raw_values.items():
                value = value_str.strip() if isinstance(value_str, str) else value_str
                if value == '' or (isinstance(value, str) and value.lower() == 'none'):
                    value = None

                if field_name in ['yahoo_ticker', 'underlying_names', 'underlying_currencies']:
                    result_data[field_name] = [item.strip() for item in value.split(';')] if value else []

                elif field_name == 'prezzi_iniziali_sottostanti':
                    if not value:
                        result_data[field_name] = []
                    else:
                        prices = []
                        price_strings = value.split(';')
                        for p_str in price_strings:
                            if not p_str.strip(): continue
                            clean_str = p_str.strip().replace('.', '').replace(',', '.')
                            prices.append(float(clean_str))
                        result_data[field_name] = prices

                elif field_name == 'dividend_yields':
                    if not value:
                        result_data[field_name] = []
                    else:
                        yields = [float(y.strip().replace(',', '.')) / 100.0 for y in value.split(';')]
                        result_data[field_name] = yields

                elif field_name in ['risk_free_rate', 'coupon_rate', 'coupon_barrier', 'capital_barrier', 'airbag_level', 'dynamic_barrier_start_level', 'step_down_rate', 'dynamic_barrier_end_level']:
                    result_data[field_name] = float(value.replace(',', '.')) / 100.0 if value is not None else None

                elif field_name == 'notional':
                    result_data[field_name] = float(value.replace(',', '.')) if value is not None else None
                elif field_name == 'observation_delay_months':
                    result_data[field_name] = int(value) if value is not None else None

                elif field_name in ['memory_feature', 'airbag_feature', 'dynamic_barrier_feature']:
                    result_data[field_name] = (str(value).lower() == 'true')
                else:
                    result_data[field_name] = value

        except (ValueError, TypeError) as e:
            messagebox.showerror("Errore di Input", f"Il valore '{value_str}' per il campo '{field_name}' non è valido.\nErrore: {e}")
            return

        if result_data.get('capital_barrier_type') == 'dynamic':
            result_data['dynamic_barrier_feature'] = True
        else:
            result_data['dynamic_barrier_feature'] = False

        if result_data.get('dynamic_barrier_feature'):
            print("▶️ Esecuzione controllo coerenza barriera dinamica...")

            temp_dates = self._generate_temp_coupon_dates(result_data)

            if temp_dates is None:
                print("❌ Salvataggio annullato a causa di input non validi per il calcolo delle date.")
                return

            user_end_level = result_data.get('dynamic_barrier_end_level')
            if user_end_level is not None:
                expected_end_level = self._calculate_expected_end_barrier(result_data, temp_dates)

                if expected_end_level is not None:
                    if not math.isclose(user_end_level, expected_end_level, rel_tol=1e-5):
                        msg = (f"ATTENZIONE: Il Livello Finale della barriera inserito è incoerente.\n\n"
                               f" • Livello Finale Inserito: {user_end_level*100:.2f}%\n"
                               f" • Livello Finale Calcolato: {expected_end_level*100:.2f}%\n"
                               f"   (basato su {len(temp_dates)} date di osservazione)\n\n"
                               f"Salvare comunque con il valore inserito?")

                        if not messagebox.askyesno("Coerenza Dati Barriera", msg):
                            print("❌ Salvataggio annullato dall'utente per incoerenza barriera.")
                            return
                    else:
                        print(f"✅ Coerenza barriera dinamica verificata ({len(temp_dates)} date).")
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
                self.fields['airbag_level'].delete(0, tk.END)
                self.fields['airbag_notes'].delete('1.0', tk.END)

    def _on_capital_barrier_type_changed(self, event=None):
        """Abilita/disabilita i campi della barriera dinamica in base alla selezione del tipo di barriera capitale."""
        if hasattr(self, 'fields') and 'capital_barrier_type' in self.fields and hasattr(self, 'dynamic_barrier_params_frame'):
            selected_type = self.fields['capital_barrier_type'].get()
            is_dynamic = (selected_type == 'dynamic')

            if is_dynamic:
                self.dynamic_barrier_params_frame.pack(fill='x', padx=10, pady=5)
                if 'dynamic_barrier_start_level' in self.fields and 'capital_barrier' in self.fields:
                    capital_barrier_val = self.fields['capital_barrier'].get().strip()
                    self.fields['dynamic_barrier_start_level'].config(state=tk.NORMAL)
                    self.fields['dynamic_barrier_start_level'].delete(0, tk.END)
                    if capital_barrier_val:
                        self.fields['dynamic_barrier_start_level'].insert(0, capital_barrier_val)
                for field_name in ['step_down_rate', 'dynamic_barrier_end_level']:
                    if field_name in self.fields:
                        self.fields[field_name].config(state=tk.NORMAL)
            else:
                self.dynamic_barrier_params_frame.pack_forget()
                for field_name in ['dynamic_barrier_start_level', 'step_down_rate', 'dynamic_barrier_end_level']:
                    if field_name in self.fields:
                        self.fields[field_name].config(state=tk.DISABLED)
                        self.fields[field_name].delete(0, tk.END)

    def _update_dependency_description(self, event=None):
        """Aggiorna la descrizione del tipo di dipendenza sottostante."""
        if hasattr(self, 'fields') and 'underlying_dependency_type' in self.fields:
            selected_type = self.fields['underlying_dependency_type'].get()
            description = self._dependency_descriptions.get(selected_type, "Descrizione non disponibile.")
            formatted_description = textwrap.fill(description, width=100)
            self.dependency_description_label.config(text=formatted_description)

class ParameterOverrideDialog:
    """
    ### MODIFICATO v1.9 ###
    Dialog per l'override dei parametri. Ora rileva se i valori sono stati
    effettivamente modificati dall'utente e restituisce un dizionario
    con lo stato dell'operazione.
    """
    def __init__(self, parent, certificate_instance, last_overrides=None):
        # Il risultato è un dizionario per contenere più informazioni
        self.result = {'cancelled': True, 'was_changed': False, 'overrides': None}
        self.parent = parent
        self.instance = certificate_instance
        self.last_overrides = last_overrides if last_overrides else {}

        # Memorizziamo i valori iniziali per rilevare le modifiche
        self.initial_values_numeric = {
            'volatilita': self.instance.parametri_mercato.get('volatilita', []),
            'dividendi': self.instance.parametri_mercato.get('dividendi', [])
        }
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Override Parametri Analisi")
        self.dialog.geometry("750x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.entries = {'volatilita': [], 'dividendi': []}
        self.underlyings = self.instance.underlying_assets

        self._setup_widgets()
        self.dialog.wait_window()

    def _setup_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        info_label = "Modifica i parametri per una simulazione 'What-If'. Lascia un campo vuoto per usare il valore attuale. Se non modifichi nulla, verrà eseguita e salvata un'analisi standard."
        ttk.Label(main_frame, text=info_label, wraplength=730, font=("Arial", 9, "italic")).pack(pady=(0, 15))

        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill=tk.X)

        ttk.Label(grid_frame, text="Sottostante", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Label(grid_frame, text="Vol. Attuale", font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky=tk.E, padx=5)
        ttk.Label(grid_frame, text="Vol. Override (%)", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.E, padx=5)
        ttk.Label(grid_frame, text="Div. Attuale", font=('Arial', 10, 'bold')).grid(row=0, column=3, sticky=tk.E, padx=5)
        ttk.Label(grid_frame, text="Div. Override (%)", font=('Arial', 10, 'bold')).grid(row=0, column=4, sticky=tk.E, padx=5)
        grid_frame.columnconfigure(0, weight=3)
        for i in range(1, 5): grid_frame.columnconfigure(i, weight=1)

        params = self.instance.parametri_mercato
        last_vols = self.last_overrides.get('volatilita', [])
        last_divs = self.last_overrides.get('dividendi', [])

        for i, asset in enumerate(self.underlyings):
            vol_entry = ttk.Entry(grid_frame, width=12, justify='right')
            # Popola con l'ultimo override, se esiste, altrimenti con il valore attuale
            val_to_show = last_vols[i] if i < len(last_vols) else self.initial_values_numeric['volatilita'][i]
            vol_entry.insert(0, f"{(val_to_show * 100):.2f}")
            self.entries['volatilita'].append(vol_entry)

        for i, asset in enumerate(self.underlyings):
            div_entry = ttk.Entry(grid_frame, width=12, justify='right')
            val_to_show = last_divs[i] if i < len(last_divs) else self.initial_values_numeric['dividendi'][i]
            div_entry.insert(0, f"{(val_to_show * 100):.2f}")
            self.entries['dividendi'].append(div_entry)

        for i, asset in enumerate(self.underlyings):
            row = i + 1
            ttk.Label(grid_frame, text=asset, anchor="w").grid(row=row, column=0, sticky="ew", padx=5)
            vol_attuale_val = params['volatilita'][i]
            ttk.Label(grid_frame, text=f"{(vol_attuale_val * 100):.2f}%", anchor="e").grid(row=row, column=1, padx=5, sticky="ew")
            self.entries['volatilita'][i].grid(row=row, column=2, padx=5)
            div_attuale_val = params['dividendi'][i]
            ttk.Label(grid_frame, text=f"{(div_attuale_val * 100):.2f}%", anchor="e").grid(row=row, column=3, padx=5, sticky="ew")
            self.entries['dividendi'][i].grid(row=row, column=4, padx=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        ttk.Button(button_frame, text="Annulla", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Esegui Analisi", command=self._apply_and_close).pack(side=tk.RIGHT)

    def _apply_and_close(self):
        """Valida gli input, rileva se sono cambiati, e imposta il risultato."""
        final_overrides = {'volatilita': [], 'dividendi': []}
        was_changed = False

        try:
            params = self.instance.parametri_mercato
            for i in range(len(self.underlyings)):
                # Gestione Volatilità
                vol_str = self.entries['volatilita'][i].get().strip()
                current_vol = float(vol_str.replace(',', '.')) / 100.0 if vol_str else params['volatilita'][i]
                final_overrides['volatilita'].append(current_vol)
                if not math.isclose(current_vol, self.initial_values_numeric['volatilita'][i], rel_tol=1e-5):
                    was_changed = True

                # Gestione Dividendi
                div_str = self.entries['dividendi'][i].get().strip()
                current_div = float(div_str.replace(',', '.')) / 100.0 if div_str else params['dividendi'][i]
                final_overrides['dividendi'].append(current_div)
                if not math.isclose(current_div, self.initial_values_numeric['dividendi'][i], rel_tol=1e-5):
                    was_changed = True

            self.result = {'cancelled': False, 'was_changed': was_changed, 'overrides': final_overrides}
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Errore di Input", "Assicurati che tutti i valori inseriti siano numeri validi (es. 10 o 35.5).", parent=self.dialog)

class SimulationSettingsDialog:
    """Dialog per modificare il numero di simulazioni per la sessione corrente."""
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent.root)
        self.dialog.title("Impostazioni Simulazione")
        self.dialog.geometry("480x200")
        self.dialog.transient(parent.root)
        self.dialog.grab_set()

        self.main_analysis_var = tk.StringVar(value=str(parent.n_sim_main_analysis))
        self.sensitivity_var = tk.StringVar(value=str(parent.n_sim_sensitivity))

        self._setup_widgets()
        self.dialog.wait_window()

    def _setup_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="Modifica il numero di percorsi per le analisi Monte Carlo.", wraplength=450).pack(pady=(0, 10))

        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill=tk.X, pady=5)

        ttk.Label(settings_frame, text="Simulazioni Analisi Standard / What-If:", width=40).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.main_analysis_var, width=15).grid(row=0, column=1, sticky=tk.E, pady=5)

        ttk.Label(settings_frame, text="Simulazioni Analisi Sensitività:", width=40).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.sensitivity_var, width=15).grid(row=1, column=1, sticky=tk.E, pady=5)

        settings_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))
        ttk.Button(button_frame, text="Annulla", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Salva Impostazioni", command=self._apply_settings).pack(side=tk.RIGHT)

    def _apply_settings(self):
        try:
            new_main = int(self.main_analysis_var.get())
            new_sensitivity = int(self.sensitivity_var.get())

            if new_main <= 0 or new_sensitivity <= 0:
                raise ValueError("Il numero di simulazioni deve essere positivo.")

            self.parent.n_sim_main_analysis = new_main
            self.parent.n_sim_sensitivity = new_sensitivity

            print(f"🔧 Impostazioni simulazione aggiornate: Analisi Principale={new_main}, Sensitività={new_sensitivity}")
            messagebox.showinfo("Successo", "Impostazioni di simulazione aggiornate per la sessione corrente.", parent=self.dialog)
            self.dialog.destroy()
        except ValueError as e:
            messagebox.showerror("Errore di Input", f"Inserire solo numeri interi positivi.\n{e}", parent=self.dialog)

class SimpleCertificateGUIManagerV15_1_Corrected:
    """*** GUI MANAGER v1.9 *** - Logica analisi Standard/What-If"""

    _dependency_descriptions = {
        'Worst-Of': "🔻 WORST-OF: Il peggiore tra tutti determina il payoff (MASSIMO RISCHIO). Performance = MIN(asset1, asset2, asset3, ...) - Basta che uno crolli!",
        'Best-Of': "🔺 BEST-OF: Il migliore tra tutti determina il payoff (MINIMO RISCHIO). Performance = MAX(asset1, asset2, asset3, ...) - Uno solo deve andare bene.",
        'Average': "📈 AVERAGE/BASKET: Performance media ponderata (RISCHIO INTERMEDIO). Performance = MEDIA(asset1, asset2, asset3, ...) - Compensazione reciproca.",
        'Single': "🌈 RAINBOW/INDIVIDUAL: Ogni asset contribuisce individualmente. Payoff calcolato per singolo sottostante - Struttura complessa.",
        'Basket Custom': "🌈 RAINBOW/INDIVIDUAL: Ogni asset contribuisce individualmente. Payoff calcolato per singolo sottostanti - Struttura complessa."
    }

    def __init__(self):
            self.root = tk.Tk()
            self.root.title("Sistema Certificati v1.9 - Logica Analisi Unificata")
            self.root.geometry("1400x900")

            self.logger = logging.getLogger(__name__)
            self.last_overrides = {}
            self.last_what_if_results = {}
            
            self.n_sim_main_analysis = 10000
            self.n_sim_sensitivity  = 5000
            self.last_sensitivity_results = {}

            self.cert_file = Path("src/app/data/certificates.json")

            print("▶️  Inizializzazione del Manager Enhanced come sorgente dati principale...")
            if ENHANCED_MANAGER_AVAILABLE:
                self.enhanced_manager = EnhancedCertificateManagerV15(config_dir=self.cert_file.parent)
                self.certificates = self.enhanced_manager.configurations
                print(f"✅ Enhanced Manager v15 inizializzato con {len(self.certificates)} certificati.")
            else:
                self.enhanced_manager = None
                self.certificates = self._load_certificates()
                print("⚠️  Enhanced Manager non disponibile. Gestione certificati locale.")

            try:
                from app.core.portfolio_manager import PortfolioManager, PortfolioGUIManager
                self.portfolio_manager = PortfolioManager(self.cert_file.parent)
                self.portfolio_gui = PortfolioGUIManager(self.portfolio_manager, self.root, self.certificates)
                print("✅ Portfolio Manager e GUI Manager inizializzati.")
            except ImportError as e:
                print(f"⚠️ Portfolio Manager non disponibile: {e}")
                self.portfolio_manager = None
                self.portfolio_gui = None

            self._setup_gui_v15_1_corrected()
            self._refresh_certificate_list()
            print("🚀 === GUI MANAGER v1.9 INIZIALIZZATO ===")

    def _open_simulation_settings(self):
        """Apre il dialog per modificare le impostazioni di simulazione."""
        SimulationSettingsDialog(self)

    def get_selected_certificate_id(self):
            """Restituisce l'ISIN del certificato selezionato nel treeview, o None se non c'è selezione."""
            selection = self.tree.selection()
            if selection:
                return self.tree.item(selection[0])['values'][0]
            return None

    def _setup_gui_v15_1_corrected(self):
        """Setup GUI completa v1.9"""

        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(toolbar, text="➕ Nuovo Certificato",
                  command=self._new_certificate).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="✏️ Modifica",
                  command=self._edit_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="🗑️ Elimina",
                  command=self._delete_selected).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        if self.enhanced_manager:
            ttk.Button(toolbar, text="📅 Calc Date",
                      command=self._calculate_dates_integrated).pack(side=tk.LEFT, padx=(0, 5))
        
        ### NUOVA CONFIGURAZIONE CON PULSANTE UNICO ###
        ttk.Button(toolbar, text="🔬 Analizza...", command=self._analyze_selected_certificate).pack(side=tk.LEFT, padx=(0, 5))
        self.analyze_sensitivity_button = ttk.Button(toolbar, text="📈 Sensitivity Analysis", command=self.run_sensitivity_analysis)
        self.analyze_sensitivity_button.pack(side=tk.LEFT, padx=(0,5))

        ttk.Button(toolbar, text="📊 Esporta Analisi Excel",
                  command=self._export_analysis_excel).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(toolbar, text="💾 Salva Tutti",
                  command=self._save_certificates).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="⚙️ Impostazioni Simulazione",
                command=self._open_simulation_settings).pack(side=tk.LEFT, padx=(0, 5))

        if hasattr(self, 'portfolio_gui') and self.portfolio_gui is not None:
            ttk.Button(toolbar, text="📁 Portfolio Manager",
                       command=self._open_portfolio_manager).pack(side=tk.LEFT, padx=(10, 5))
        else:
            print("⚠️  Portfolio Manager non disponibile. Pulsante disabilitato.")
            ttk.Button(toolbar, text="📁 Portfolio Manager (non disponibile)", state="disabled").pack(side=tk.LEFT, padx=(10, 5))

        system_buttons_frame = ttk.Frame(toolbar)
        system_buttons_frame.pack(side=tk.RIGHT)
        ttk.Button(system_buttons_frame, text="🚪 Esci", command=self.close).pack(side=tk.LEFT)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(paned, text="📋 Certificati")
        paned.add(list_frame, weight=1)

        columns = ("ISIN", "Nome", "Tipo", "Emittente", "Risk-Free %", "Scadenza", "Stato")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            if col == "ISIN": self.tree.column(col, width=120)
            elif col == "Nome": self.tree.column(col, width=200)
            elif col == "Risk-Free %": self.tree.column(col, width=70)
            elif col == "Scadenza": self.tree.column(col, width=90)
            elif col == "Stato": self.tree.column(col, width=65)
            else: self.tree.column(col, width=120)

        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=list_scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self._edit_selected)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)

        details_frame = ttk.LabelFrame(paned, text="📊 Dettagli Certificato")
        paned.add(details_frame, weight=1)

        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.details_text = tk.Text(text_frame, wrap=tk.WORD, font=("Courier", 10))
        details_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_var = tk.StringVar()
        self.status_var.set("Sistema Certificati v1.9 - Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def run_sensitivity_analysis(self):
        """Esegue l'analisi di sensitività sulla volatilità per il certificato selezionato."""
        selected_id = self.get_selected_certificate_id()
        if not selected_id:
            messagebox.showwarning("Nessuna Selezione", "Selezionare un certificato da analizzare.")
            return

        try:
            self.status_var.set(f"🔬 Preparazione analisi di sensitività per {selected_id}...")
            self.root.update_idletasks()

            certificate_instance = self.enhanced_manager.create_certificate_instance_from_config(selected_id)

            if not certificate_instance:
                messagebox.showerror("Errore Preparazione", f"Impossibile preparare il certificato {selected_id} per l'analisi. Controllare i log.")
                return

            volatility_multipliers = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
            analyzer = UnifiedCertificateAnalyzer(certificate_instance)

            self.status_var.set(f"🔬 Analisi di sensitività in corso...")
            self.root.update_idletasks()

            results = analyzer.analyze_parameter_sensitivity('volatilita', volatility_multipliers, n_simulations=self.n_sim_sensitivity)

            self.last_sensitivity_results[selected_id] = results
            self.show_sensitivity_results(results)
            self._display_certificate_details(selected_id)

        except Exception as e:
            messagebox.showerror("Errore Analisi", f"Si è verificato un errore durante l'analisi di sensitività:\n{e}")
            self.logger.error(f"Errore durante l'analisi di sensitività: {e}", exc_info=True)
        finally:
            self.status_var.set("Pronto.")

    def show_sensitivity_results(self, results_data: dict):
        """Mostra i risultati dell'analisi di sensitività in una finestra di dialogo."""
        report_text = "Analisi di Sensitività - Impatto della Volatilità\n"
        report_text += "="*60 + "\n\n"
        report_text += f"Fair Value di Base (Volatilità 100%): €{results_data['base_fair_value']:.2f}\n\n"

        report_text += "{:<20} {:<20} {:<20}\n".format("Moltiplicatore Vol.", "Fair Value Risultante", "Variazione %")
        report_text += "-"*60 + "\n"

        for res in results_data['results']:
            if 'error' in res:
                report_text += f"Errore con moltiplicatore {res['parameter_value']}\n"
            else:
                fv_str = f"€{res['fair_value']:.2f}"
                change_str = f"{res['change_pct']:.2%}"
                report_text += "{:<20} {:<20} {:<20}\n".format(res['label'], fv_str, change_str)

        results_window = tk.Toplevel(self.root)
        results_window.title("Risultati Analisi di Sensitività")
        results_window.geometry("550x350")
        results_window.transient(self.root)
        results_window.grab_set()

        text_widget = tk.Text(results_window, wrap=tk.WORD, font=("Courier", 10))
        text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        text_widget.insert(tk.END, report_text)
        text_widget.config(state=tk.DISABLED)

        close_button = ttk.Button(results_window, text="Chiudi", command=results_window.destroy)
        close_button.pack(pady=5)

    def _open_portfolio_manager(self):
        """Apre la finestra del Portfolio Manager."""
        if not hasattr(self, 'portfolio_gui') or self.portfolio_gui is None:
            messagebox.showerror("Errore", "Portfolio Manager non inizializzato.")
            return

        try:
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
        enhanced_config_obj = self.certificates.get(cert_id)
        if not enhanced_config_obj:
            messagebox.showerror("Errore", f"Certificato {cert_id} non trovato")
            return

        print(f"📅 === CALC DATE INTEGRATA per l'oggetto {cert_id} ===")
        try:
            if self.enhanced_manager:
                cert_data_as_dict = vars(copy.deepcopy(enhanced_config_obj.base_config))
                dialog = CalculoDateAutoDialogV15(
                    self.root,
                    selected_certificate_id=cert_id,
                    configurations={cert_id: cert_data_as_dict}
                )
                self.root.wait_window(dialog.dialog)
                if hasattr(dialog, 'result') and dialog.result:
                    print(f"📅 Date calcolate per {cert_id}. Aggiornamento in corso...")
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
            dialog = EnhancedCertificateDialogV15_1_Corrected(self.root, "Nuovo Certificato", self.enhanced_manager)
            if hasattr(dialog, 'result') and dialog.result:
                cert_data = dialog.result
                cert_id = cert_data['isin']
                print(f"💾 Creazione certificato {cert_id}")
                if cert_id in self.certificates:
                    if not messagebox.askyesno("ISIN Esistente", f"Certificato {cert_id} già esistente. Sovrascrivere?"):
                        return
                self.enhanced_manager.add_certificate_from_dict_v15(cert_id, cert_data)
                if self._save_certificates():
                    self._refresh_certificate_list()
                    self._reselect_tree_item(cert_id)
                    messagebox.showinfo("Successo", f"Certificato {cert_id} creato con successo!")
                else:
                    messagebox.showerror("Errore", f"Impossibile salvare certificato {cert_id}")
            else:
                print("ℹ️ Dialog nuovo certificato annullato")
        except Exception as e:
            self.logger.error(f"Errore creazione certificato: {e}", exc_info=True)
            messagebox.showerror("Errore", f"Errore creazione certificato:\n{e}")

    def _edit_selected(self, event=None):
        """
        Modifica il certificato selezionato, invalidando i risultati delle analisi.
        """
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da modificare.")
            return

        selected_isin = self.tree.item(selection[0])['values'][0]
        cert_data_dict = self.enhanced_manager.get_certificate_data_for_gui(selected_isin)
        if not cert_data_dict:
            messagebox.showerror("Errore", "Dati del certificato non trovati.")
            return

        print(f"✏️ === MODIFICA CERTIFICATO {selected_isin} v15.1 CORRECTED ===")
        try:
            dialog = EnhancedCertificateDialogV15_1_Corrected(self.root, f"Modifica {selected_isin}", self.enhanced_manager, cert_data_dict)
            if hasattr(dialog, 'result') and dialog.result:
                updated_data = dialog.result
                cert_id = updated_data['isin']
                
                # Invalida i risultati dell'analisi di base
                enhanced_config_obj = self.enhanced_manager.configurations.get(cert_id)
                if enhanced_config_obj and hasattr(enhanced_config_obj, 'analysis_results') and enhanced_config_obj.analysis_results:
                    print(f"✏️ Invalidazione risultati analisi per {cert_id} a seguito di modifica.")
                    enhanced_config_obj.analysis_results['is_valid'] = False
                
                # Invalida i risultati temporanei
                if cert_id in self.last_what_if_results:
                    del self.last_what_if_results[cert_id]
                    print(f"✏️ Invalidazione risultati what-if per {cert_id}.")
                if cert_id in self.last_sensitivity_results:
                    del self.last_sensitivity_results[cert_id]
                    print(f"✏️ Invalidazione risultati sensitività per {cert_id}.")

                self.enhanced_manager.add_certificate_from_dict_v15(cert_id, updated_data)
                self._save_certificates()
                self._refresh_certificate_list()
                self._reselect_tree_item(cert_id)
                messagebox.showinfo("Successo", f"Certificato {cert_id} modificato con successo!")
            else:
                print(f"❌ Dialog di modifica annullato.")
        except Exception as e:
            self.logger.error(f"Errore durante la modifica di {selected_isin}: {e}", exc_info=True)
            messagebox.showerror("Errore Modifica", f"Si è verificato un errore imprevisto:\n{e}")

    def _refresh_certificate_list(self):
        """Refresh lista certificati accedendo correttamente agli attributi dell'oggetto."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for cert_id, enhanced_config in self.certificates.items():
            if enhanced_config:
                cert_data = enhanced_config.base_config
                risk_free_rate = getattr(cert_data, 'risk_free_rate', 0)
                rf_display = f"{risk_free_rate * 100:.2f}%" if isinstance(risk_free_rate, (int, float)) and risk_free_rate <= 1.0 else f"{risk_free_rate:.2f}%"
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
        self.status_var.set(f"Sistema Certificati v1.9 - {len(self.certificates)} certificati caricati")

    def _reselect_tree_item(self, cert_id_to_select: str):
        """Scorre il treeview e riseleziona la riga corrispondente all'ISIN fornito."""
        for item_id in self.tree.get_children():
            item_values = self.tree.item(item_id, 'values')
            if item_values and item_values[0] == cert_id_to_select:
                self.tree.selection_set(item_id)
                self.tree.focus(item_id)
                self.tree.see(item_id)
                self._on_selection_changed()
                break

    def _on_selection_changed(self, event=None):
        """Gestione selezione certificato"""
        selection = self.tree.selection()
        if selection:
            cert_id = self.tree.item(selection[0])['values'][0]
            self._display_certificate_details(cert_id)

    def _display_certificate_details(self, cert_id):
        """
        ### MODIFICATO v1.9 ###
        Visualizza i dettagli con la nuova logica:
        1. Mostra sempre l'analisi di base salvata.
        2. Mostra l'analisi 'what-if' solo se presente nella sessione corrente.
        3. Mostra l'analisi di sensitività solo se presente nella sessione corrente.
        """
        if cert_id not in self.certificates:
            return
        
        enhanced_config = self.certificates[cert_id]
        if enhanced_config is None: return
        cert_data = enhanced_config.base_config

        def format_percentage(value, decimals=2):
            if isinstance(value, (int, float)):
                return f"{value * 100:.{decimals}f}%"
            return str(value) if value is not None else 'N/A'

        def get_attr(obj, attr_name, default='N/A'):
            val = getattr(obj, attr_name, default)
            return val if val is not None else default

        issue_date_obj = get_attr(cert_data, 'issue_date')
        maturity_date_obj = get_attr(cert_data, 'maturity_date')
        issue_date_str = issue_date_obj.strftime('%Y-%m-%d') if isinstance(issue_date_obj, datetime) else issue_date_obj
        maturity_date_str = maturity_date_obj.strftime('%Y-%m-%d') if isinstance(maturity_date_obj, datetime) else maturity_date_obj

        rf_display = format_percentage(get_attr(cert_data, 'risk_free_rate', 0))
        airbag_feature = get_attr(cert_data, 'airbag_feature', False)
        airbag_level_str = format_percentage(get_attr(cert_data, 'airbag_level', 0)) if airbag_feature else "N/A"
        airbag_notes = get_attr(cert_data, 'airbag_notes', '') or ''
        note_barriere = get_attr(cert_data, 'note_barriere', '') or ''
        
        details = f"""DETTAGLI CERTIFICATO v1.9
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
        if airbag_notes: details += f"Note Airbag: {airbag_notes}\n"
        details += f"""
BARRIERE:
Barriera Cedola: {format_percentage(get_attr(cert_data, 'coupon_barrier', 0))} ({get_attr(cert_data, 'coupon_barrier_type')})
Barriera Capitale: {format_percentage(get_attr(cert_data, 'capital_barrier', 0))} ({get_attr(cert_data, 'capital_barrier_type')})
"""
        if note_barriere: details += f"Note Barriere: {note_barriere}\n"
        
        if get_attr(cert_data, 'dynamic_barrier_feature', False):
            details += f"""
BARRIERE DINAMICHE:
Abilitata: True
Livello Iniziale: {format_percentage(get_attr(cert_data, 'dynamic_barrier_start_level', 0))}
Step Down Rate: {format_percentage(get_attr(cert_data, 'step_down_rate', 0), decimals=3)}
Livello Finale: {format_percentage(get_attr(cert_data, 'dynamic_barrier_end_level', 0))}
Mesi di Ritardo Osservazione: {get_attr(cert_data, 'observation_delay_months')}
"""

        details += f"\nSOTTOSTANTI:\n"
        underlying_tickers = get_attr(cert_data, 'yahoo_ticker', [])
        initial_prices = get_attr(cert_data, 'prezzi_iniziali_sottostanti', [])
        currencies = get_attr(cert_data, 'underlying_currencies', [])
        
        if underlying_tickers:
            header = f"  {'Ticker':<15} {'Prezzo Iniziale':>18} {'Valuta':>8}\n"
            details += header
            details += f"  {'-'*15:<15} {'-'*18:>18} {'-'*8:>8}\n"
            
            for i, ticker in enumerate(underlying_tickers):
                price = f"{initial_prices[i]:,.2f}" if i < len(initial_prices) else "N/A"
                currency = currencies[i] if i < len(currencies) else "N/A"
                details += f"  {ticker:<15} {price:>18} {currency:>8}\n"
        
        details += f"Tipo Dipendenza: {get_attr(cert_data, 'underlying_dependency_type')}\n"

        # --- INIZIO BLOCCO VISUALIZZAZIONE ANALISI (Logica Definitiva v1.9) ---
        
        # 1. Mostra l'analisi di base salvata (se valida)
        saved_analysis = getattr(enhanced_config, 'analysis_results', None)
        if saved_analysis and saved_analysis.get('is_valid', True):
            timestamp_str = "N/A"
            if 'analysis_timestamp' in saved_analysis:
                try:
                    timestamp_str = datetime.fromisoformat(saved_analysis['analysis_timestamp']).strftime('%d/%m/%Y %H:%M')
                except (ValueError, TypeError):
                    timestamp_str = "Data non valida"

            details += f"""
{'='*60}
📊 ANALISI DI BASE (salvata il {timestamp_str})

Prezzo di Mercato:       € {saved_analysis.get('certificate_market_price', 'N/A')}
Fair Value Stimato:      € {saved_analysis.get('fair_value', 'N/A')}
Fair Value (Naked):      € {saved_analysis.get('fair_value_naked', 'N/A')}
Costo Implicito Protez.: € {saved_analysis.get('protection_implicit_cost', 'N/A')}

Volatilità Stimata:      {saved_analysis.get('volatility', 'N/A')}
Prob. Rottura Barriera:  {saved_analysis.get('barrier_breach_probability', 'N/A')}
VaR 95%:                 {saved_analysis.get('var_95', 'N/A')}
"""
        else:
            details += f"""
{'='*60}
📊 ANALISI DI BASE
Nessuna analisi valida salvata per questo certificato.
Premere 'Analizza' per eseguire una nuova valutazione.
"""

        # 2. Mostra l'ultima analisi "What-If" (se esiste per la sessione corrente)
        what_if_data = self.last_what_if_results.get(cert_id)
        if what_if_data:
            results = what_if_data['results']
            overrides = what_if_data['overrides']
            base_params = what_if_data['base_params_for_comparison']
            sims_used = what_if_data.get('simulations_used', self.n_sim_main_analysis)
            
            timestamp_str = "N/A"
            if 'analysis_timestamp' in results:
                try:
                    timestamp_str = datetime.fromisoformat(results['analysis_timestamp']).strftime('%d/%m/%Y %H:%M:%S')
                except (ValueError, TypeError):
                    timestamp_str = "Data non valida"
            
            details += f"""
{'='*60}
🔬 ANALISI 'WHAT-IF' (Temporanea - del {timestamp_str})
Simulazioni: {sims_used:,}

Fair Value Stimato:      € {results.get('fair_value', 'N/A')}
Prob. Rottura Barriera:  {results.get('barrier_breach_probability', 'N/A')}

Parametri Manuali Applicati:"""

            changed_params_text = ""
            base_vols = base_params.get('volatilita', [])
            base_divs = base_params.get('dividendi', [])
            override_vols = overrides.get('volatilita', [])
            override_divs = overrides.get('dividendi', [])

            for i, asset in enumerate(get_attr(cert_data, 'yahoo_ticker', [])):
                param_changed = False
                asset_text = f"\n     • {asset}:"
                if i < len(base_vols) and i < len(override_vols) and not math.isclose(base_vols[i], override_vols[i]):
                    asset_text += f" Vol={override_vols[i]:.2%}"
                    param_changed = True
                if i < len(base_divs) and i < len(override_divs) and not math.isclose(base_divs[i], override_divs[i]):
                    asset_text += f" Div={override_divs[i]:.2%}"
                    param_changed = True
                if param_changed:
                    changed_params_text += asset_text

            if not changed_params_text:
                details += " Nessun override applicato (usati valori di base)."
            else:
                details += changed_params_text

        # 3. Mostra l'analisi di sensitività (se presente nella sessione corrente)
        sensitivity_data = self.last_sensitivity_results.get(cert_id)
        if sensitivity_data:
            sims_used_sensitivity = self.n_sim_sensitivity
            timestamp_str = "N/A"
            if 'analysis_timestamp' in sensitivity_data:
                try:
                    timestamp_str = datetime.fromisoformat(sensitivity_data['analysis_timestamp']).strftime('%d/%m/%Y %H:%M:%S')
                except (ValueError, TypeError):
                    timestamp_str = "Data non valida"
            
            details += f"""
{'='*60}
📈 ANALISI DI SENSITIVITÀ (Temporanea - del {timestamp_str})
Simulazioni: {sims_used_sensitivity:,}
Fair Value di Base (Volatilità 100%): €{sensitivity_data['base_fair_value']:.2f}

{'Moltiplicatore':<15} {'Fair Value':>15} {'Variazione':>15}
{'-'*15:<15} {'-'*15:>15} {'-'*15:>15}
"""
            for res in sensitivity_data['results']:
                fv_str = f"€{res['fair_value']:.2f}"
                change_str = f"{res['change_pct']:.2%}"
                details += f"{res['label']:<15} {fv_str:>15} {change_str:>15}\n"
        
        # --- FINE BLOCCO VISUALIZZAZIONE ANALISI ---

        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)

    def _load_certificates(self):
        """Carica certificati da file JSON."""
        if not self.cert_file.exists():
            return {}
        try:
            with open(self.cert_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            messagebox.showerror("Errore Caricamento", f"Errore caricamento certificati:\n{e}")
            return {}

    def _save_certificates(self):
        """Salva tutti i certificati DELEGANDO l'operazione al manager."""
        if self.enhanced_manager:
            try:
                self.enhanced_manager.save_all_certificates()
                self.status_var.set(f"Salvataggio completato con successo tramite manager.")
                print("✅ Salvataggio delegato al manager completato.")
                return True
            except Exception as e:
                self.logger.error(f"Errore durante il salvataggio delegato al manager: {e}", exc_info=True)
                messagebox.showerror("Errore Salvataggio", f"Il manager ha riscontrato un errore durante il salvataggio:\n{e}")
                return False
        else:
            print("⚠️  Manager non disponibile, si procede con il salvataggio locale (legacy).")
            try:
                if self.cert_file.exists():
                    backup_file = self.cert_file.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                    import shutil
                    shutil.copy2(self.cert_file, backup_file)
                with open(self.cert_file, 'w', encoding='utf-8') as f:
                    json.dump(self.certificates, f, ensure_ascii=False, indent=2, default=str)
                self.status_var.set(f"Salvataggio locale (fallback) completato.")
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
        if messagebox.askyesno("Conferma Eliminazione", f"Eliminare definitivamente il certificato {cert_id}?"):
            if self.enhanced_manager.delete_certificate(cert_id):
                if self._save_certificates():
                    self._refresh_certificate_list()
                    self.details_text.delete(1.0, tk.END)
                    messagebox.showinfo("Eliminato", f"Certificato {cert_id} eliminato")

    def _analyze_selected_certificate(self):
        """
        ### NUOVA LOGICA v1.9 ###
        Avvia l'analisi con un singolo pulsante.
        - Se l'utente non modifica i parametri, esegue e salva un'analisi standard.
        - Se l'utente modifica i parametri, esegue un'analisi "what-if" temporanea.
        """
        selected_isin = self.get_selected_certificate_id()
        if not selected_isin:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da analizzare.")
            return

        self.status_var.set(f"📊 Preparazione analisi per {selected_isin}...")
        self.root.update_idletasks()

        try:
            certificate_instance = self.enhanced_manager.create_certificate_instance_from_config(selected_isin)
            if not certificate_instance:
                messagebox.showerror("Errore Preparazione", f"Impossibile preparare il certificato {selected_isin} per l'analisi. Controllare i log.")
                self.status_var.set("Pronto.")
                return

            previous_overrides = self.last_overrides.get(selected_isin)
            override_dialog = ParameterOverrideDialog(self.root, certificate_instance, previous_overrides)
            
            dialog_result = override_dialog.result
            if dialog_result.get('cancelled', True):
                print("ℹ️ Analisi annullata dall'utente.")
                self.status_var.set("Pronto.")
                return
                
            # --- NUOVA LOGICA DECISIONALE ---
            if dialog_result['was_changed']:
                # Scenario B: Parametri modificati -> Esegui analisi "What-If"
                self.status_var.set(f"🔬 Analisi 'What-If' in corso per {selected_isin}...")
                self.root.update_idletasks()
                override_params = dialog_result['overrides']
                self.last_overrides[selected_isin] = override_params
                
                analysis_results = self.enhanced_manager.run_full_analysis_with_overrides(
                    selected_isin, override_params, n_simulations=self.n_sim_main_analysis
                )
                if analysis_results:
                    self.last_what_if_results[selected_isin] = {'results': analysis_results, 'overrides': override_params, 'base_params_for_comparison': certificate_instance.parametri_mercato, 'simulations_used': self.n_sim_main_analysis}
                    messagebox.showinfo("Analisi 'What-If' Completata", "Risultati temporanei calcolati. Controlla il pannello Dettagli.")
                    self.status_var.set("Analisi 'what-if' completata.")
            else:
                # Scenario A: Parametri non modificati -> Esegui analisi Standard
                self.status_var.set(f"📊 Analisi Standard in corso per {selected_isin}...")
                self.root.update_idletasks()
                analysis_results = self.enhanced_manager.run_and_save_standard_analysis(selected_isin, self.n_sim_main_analysis)
                if analysis_results:
                    messagebox.showinfo("Analisi Standard Completata", f"Analisi standard per {selected_isin} completata e salvata con successo.")
                    if selected_isin in self.last_what_if_results: del self.last_what_if_results[selected_isin]
                    self.status_var.set("Analisi standard completata.")
            
            # In ogni caso, aggiorna la vista
            self._display_certificate_details(selected_isin)

        except Exception as e:
            self.logger.error(f"Errore imprevisto durante l'analisi in GUI per {selected_isin}: {e}", exc_info=True)
            messagebox.showerror("Errore di Analisi", f"Si è verificato un errore imprevisto nella GUI:\n{e}")
            self.status_var.set("Analisi fallita.")

    def _export_analysis_excel(self):
        """Esporta analisi avanzata in Excel."""
        selected_isin = self.get_selected_certificate_id()
        if not selected_isin:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da esportare")
            return

        cert_data_dict = self.enhanced_manager.get_certificate_data_for_gui(selected_isin)
        if not cert_data_dict:
            messagebox.showerror("Errore", f"Dati per il certificato {selected_isin} non trovati.")
            return

        self.status_var.set(f"Esportazione Excel per {selected_isin} in corso...")
        self.root.update_idletasks()

        try:
            config = RealCertificateConfig(**cert_data_dict)
            importer = RealCertificateImporter()
            certificate_object = importer.import_certificate(config)
            analyzer = UnifiedRiskAnalyzer()
            risk_metrics = analyzer.analyze_certificate_risk(certificate_object)
            analysis_results = {
                'risk_metrics': risk_metrics.to_dict(),
                'fair_value': {} # Placeholder
            }
            exporter = AdvancedExcelExporter()
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
        if messagebox.askyesno("Chiusura", "Chiudere il Sistema Certificati?"):
            print("🚪 Chiusura GUI Certificate Manager v1.9")
            self.root.destroy()

    def run(self):
        """Avvia GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()

if __name__ == "__main__":
    print("🚀 === SISTEMA CERTIFICATI v1.9 - AVVIO ===")
    try:
        manager = SimpleCertificateGUIManagerV15_1_Corrected()
        manager.run()
    except Exception as e:
        print(f"❌ Errore avvio Sistema: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Errore Critico", f"Errore critico avvio Sistema:\n{e}")