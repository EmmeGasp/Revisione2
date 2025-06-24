# ========================================
# FIX CONFLITTO BARRIERE GUI v14.12
# Sistema Certificati Finanziari - Correzione Interfaccia
# ========================================
# File: gui_barrier_fix.py  
# Timestamp: 2025-06-16 15:10:00
# Risolve conflitto tra campi numerici e descrittivi barriere
# ========================================

"""
PROBLEMA IDENTIFICATO:
- Campo "Barriera Cedola" numerico: 0.0
- Campo "Tipo Barriera Cedola" descrittivo: "none" 
- CONFLITTO: Se tipo="none" perché c'è valore numerico?

SOLUZIONE:
1. Auto-sync tra campi numerici e descrittivi
2. Disabilitazione campi numerici quando tipo="none"
3. Validazione incrociata prima del salvataggio
4. Logic consistency enforcement
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Callable
import logging

# ========================================
# BARRIER LOGIC MANAGER
# ========================================

class BarrierLogicManager:
    """Gestisce la logica di coerenza tra campi barriera"""
    
    # Mapping tipi barriera e comportamenti
    BARRIER_TYPE_CONFIG = {
        'none': {
            'coupon_enabled': False,
            'coupon_default': 0.0,
            'description': 'Cedola incondizionata - nessuna barriera',
            'validation_required': False
        },
        'protected': {
            'coupon_enabled': True, 
            'coupon_default': 70.0,
            'description': 'Capitale garantito con barriera cedola',
            'validation_required': True,
            'min_value': 50.0,
            'max_value': 100.0
        },
        'dynamic': {
            'coupon_enabled': True,
            'coupon_default': 65.0, 
            'description': 'Barriera dinamica (step-down)',
            'validation_required': True,
            'min_value': 50.0,
            'max_value': 100.0
        },
        'american': {
            'coupon_enabled': True,
            'coupon_default': 60.0,
            'description': 'Barriera americana (controllo continuo)',
            'validation_required': True,
            'min_value': 40.0,
            'max_value': 85.0
        },
        'european': {
            'coupon_enabled': True,
            'coupon_default': 70.0,
            'description': 'Barriera europea (controllo a scadenza)',
            'validation_required': True,
            'min_value': 50.0,
            'max_value': 90.0
        }
    }
    
    @staticmethod
    def get_barrier_config(barrier_type: str) -> Dict[str, Any]:
        """Ottieni configurazione per tipo barriera"""
        return BarrierLogicManager.BARRIER_TYPE_CONFIG.get(
            barrier_type, 
            BarrierLogicManager.BARRIER_TYPE_CONFIG['none']
        )
    
    @staticmethod
    def validate_barrier_consistency(coupon_type: str, coupon_value: float,
                                   capital_type: str, capital_value: float) -> Dict[str, Any]:
        """Valida coerenza completa dei campi barriera"""
        
        errors = []
        warnings = []
        
        # Valida barriera cedola
        coupon_config = BarrierLogicManager.get_barrier_config(coupon_type)
        
        if coupon_type == 'none':
            if coupon_value != 0.0:
                errors.append(f"Barriera cedola deve essere 0.0 quando tipo è 'none' (attuale: {coupon_value})")
        else:
            if coupon_config['validation_required']:
                min_val = coupon_config.get('min_value', 0)
                max_val = coupon_config.get('max_value', 100)
                
                if not (min_val <= coupon_value <= max_val):
                    errors.append(f"Barriera cedola {coupon_value}% fuori range [{min_val}%-{max_val}%] per tipo '{coupon_type}'")
        
        # Valida barriera capitale
        capital_config = BarrierLogicManager.get_barrier_config(capital_type)
        
        if capital_type == 'none':
            if capital_value != 0.0:
                errors.append(f"Barriera capitale deve essere 0.0 quando tipo è 'none' (attuale: {capital_value})")
        else:
            if capital_config['validation_required']:
                min_val = capital_config.get('min_value', 0)
                max_val = capital_config.get('max_value', 100)
                
                if not (min_val <= capital_value <= max_val):
                    errors.append(f"Barriera capitale {capital_value}% fuori range [{min_val}%-{max_val}%] per tipo '{capital_type}'")
        
        # Validazioni incrociate
        if coupon_type != 'none' and capital_type != 'none':
            if coupon_value < capital_value:
                warnings.append(f"Barriera cedola ({coupon_value}%) < barriera capitale ({capital_value}%) - configurazione insolita")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'coupon_config': coupon_config,
            'capital_config': capital_config
        }
    
    @staticmethod
    def auto_sync_barrier_fields(barrier_type: str, current_value: Optional[float] = None) -> float:
        """Auto-sync del valore numerico basato sul tipo"""
        
        config = BarrierLogicManager.get_barrier_config(barrier_type)
        
        if not config['coupon_enabled']:
            return 0.0
        
        # Se c'è un valore corrente valido, mantienilo
        if current_value is not None and config['validation_required']:
            min_val = config.get('min_value', 0)
            max_val = config.get('max_value', 100)
            
            if min_val <= current_value <= max_val:
                return current_value
        
        # Altrimenti usa default
        return config['coupon_default']

# ========================================
# ENHANCED GUI COMPONENTS
# ========================================

class SmartBarrierFrame(ttk.Frame):
    """Frame intelligente per gestione barriere con auto-sync"""
    
    def __init__(self, parent, title: str, barrier_name: str, 
                 on_change_callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.barrier_name = barrier_name  # 'coupon' o 'capital'
        self.on_change_callback = on_change_callback
        self.logger = logging.getLogger(f"{__name__}.SmartBarrierFrame")
        
        # Variables
        self.type_var = tk.StringVar(value='none')
        self.value_var = tk.DoubleVar(value=0.0)
        self.enabled_var = tk.BooleanVar(value=False)
        
        # Bind events
        self.type_var.trace('w', self._on_type_changed)
        self.value_var.trace('w', self._on_value_changed)
        
        self._create_widgets(title)
        self._update_field_states()
    
    def _create_widgets(self, title: str):
        """Crea widgets del frame"""
        
        # Title
        title_label = ttk.Label(self, text=title, font=('Arial', 10, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 5))
        
        # Tipo barriera
        ttk.Label(self, text="Tipo:").grid(row=1, column=0, sticky='w', padx=(0, 5))
        
        self.type_combo = ttk.Combobox(
            self, 
            textvariable=self.type_var,
            values=['none', 'protected', 'dynamic', 'american', 'european'],
            state='readonly',
            width=15
        )
        self.type_combo.grid(row=1, column=1, sticky='w', padx=(0, 5))
        
        # Info tooltip
        self.info_label = ttk.Label(self, text="ℹ️", foreground='blue', cursor='hand2')
        self.info_label.grid(row=1, column=2, sticky='w')
        self.info_label.bind('<Button-1>', self._show_info)
        
        # Valore numerico
        ttk.Label(self, text="Valore (%):").grid(row=2, column=0, sticky='w', padx=(0, 5), pady=(5, 0))
        
        self.value_entry = ttk.Entry(
            self,
            textvariable=self.value_var,
            width=10,
            validate='key',
            validatecommand=(self.register(self._validate_numeric), '%P')
        )
        self.value_entry.grid(row=2, column=1, sticky='w', padx=(0, 5), pady=(5, 0))
        
        # Status indicator
        self.status_label = ttk.Label(self, text="", foreground='green')
        self.status_label.grid(row=3, column=0, columnspan=3, sticky='w', pady=(2, 0))
    
    def _on_type_changed(self, *args):
        """Callback quando cambia tipo barriera"""
        
        barrier_type = self.type_var.get()
        
        # Auto-sync valore
        current_value = self.value_var.get()
        new_value = BarrierLogicManager.auto_sync_barrier_fields(barrier_type, current_value)
        
        if new_value != current_value:
            self.value_var.set(new_value)
        
        # Aggiorna stato campi
        self._update_field_states()
        
        # Callback esterno
        if self.on_change_callback:
            self.on_change_callback(self.barrier_name, barrier_type, new_value)
        
        self.logger.debug(f"Tipo {self.barrier_name} cambiato: {barrier_type} -> valore: {new_value}")
    
    def _on_value_changed(self, *args):
        """Callback quando cambia valore numerico"""
        
        try:
            value = self.value_var.get()
            barrier_type = self.type_var.get()
            
            # Valida valore
            self._validate_current_value()
            
            # Callback esterno
            if self.on_change_callback:
                self.on_change_callback(self.barrier_name, barrier_type, value)
        
        except tk.TclError:
            # Valore non valido - ignorato
            pass
    
    def _update_field_states(self):
        """Aggiorna stato dei campi (enabled/disabled)"""
        
        barrier_type = self.type_var.get()
        config = BarrierLogicManager.get_barrier_config(barrier_type)
        
        # Abilita/disabilita campo numerico
        if config['coupon_enabled']:
            self.value_entry.configure(state='normal')
            self.status_label.configure(text="✓ Barriera attiva", foreground='green')
        else:
            self.value_entry.configure(state='disabled')
            self.status_label.configure(text="○ Nessuna barriera", foreground='gray')
        
        # Aggiorna tooltip info
        self._update_info_tooltip(config)
    
    def _validate_current_value(self):
        """Valida valore corrente e aggiorna status"""
        
        try:
            value = self.value_var.get()
            barrier_type = self.type_var.get()
            
            # Validazione completa
            validation = BarrierLogicManager.validate_barrier_consistency(
                barrier_type, value, 'none', 0.0  # Solo questo campo
            )
            
            if validation['valid']:
                self.status_label.configure(text="✓ Valore valido", foreground='green')
            else:
                error_msg = validation['errors'][0] if validation['errors'] else "Errore validazione"
                self.status_label.configure(text=f"✗ {error_msg}", foreground='red')
        
        except Exception as e:
            self.status_label.configure(text="✗ Valore non valido", foreground='red')
    
    def _validate_numeric(self, value: str) -> bool:
        """Valida input numerico"""
        
        if value == "":
            return True
        
        try:
            float_val = float(value)
            return 0.0 <= float_val <= 100.0
        except ValueError:
            return False
    
    def _show_info(self, event=None):
        """Mostra info tooltip"""
        
        barrier_type = self.type_var.get()
        config = BarrierLogicManager.get_barrier_config(barrier_type)
        
        info_text = f"Tipo: {barrier_type}\n\n{config['description']}"
        
        if config['validation_required']:
            min_val = config.get('min_value', 0)
            max_val = config.get('max_value', 100)
            info_text += f"\n\nRange valido: {min_val}% - {max_val}%"
        
        messagebox.showinfo("Info Barriera", info_text)
    
    def _update_info_tooltip(self, config: Dict[str, Any]):
        """Aggiorna tooltip informativo"""
        
        # Per ora usa semplice binding - in futuro tooltip avanzato
        pass
    
    def get_values(self) -> Dict[str, Any]:
        """Ottieni valori correnti"""
        return {
            'type': self.type_var.get(),
            'value': self.value_var.get(),
            'enabled': self.type_var.get() != 'none'
        }
    
    def set_values(self, barrier_type: str, value: float):
        """Imposta valori"""
        self.type_var.set(barrier_type)
        self.value_var.set(value)

# ========================================
# ENHANCED CERTIFICATE DIALOG
# ========================================

class EnhancedCertificateDialog(tk.Toplevel):
    """Dialog certificato migliorato con gestione barriere intelligente"""
    
    def __init__(self, parent, certificate_data: Optional[Dict] = None):
        super().__init__(parent)
        
        self.certificate_data = certificate_data or {}
        self.validation_errors = []
        
        self.title("Certificato - Configurazione Avanzata")
        self.geometry("800x900")
        self.resizable(True, True)
        
        # Rendi modale
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._load_data()
        
        # Center window
        self.center_window()
    
    def _create_widgets(self):
        """Crea widgets del dialog"""
        
        # Main frame con scrollbar
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Notebook per sezioni
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Tab 1: Info Base
        self._create_basic_info_tab(notebook)
        
        # Tab 2: Barriere (ENHANCED)
        self._create_enhanced_barriers_tab(notebook)
        
        # Tab 3: Struttura Avanzata
        self._create_advanced_structure_tab(notebook)
        
        # Tab 4: Validazione
        self._create_validation_tab(notebook)
        
        # Bottom buttons
        self._create_bottom_buttons(main_frame)
    
    def _create_basic_info_tab(self, notebook):
        """Tab informazioni base"""
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Info Base")
        
        # Standard fields - implementazione semplificata
        ttk.Label(frame, text="Info base certificate...").pack(pady=20)
    
    def _create_enhanced_barriers_tab(self, notebook):
        """Tab barriere migliorato con SmartBarrierFrame"""
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🛡️ Barriere")
        
        # Intestazione
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(
            header_frame, 
            text="Configurazione Barriere",
            font=('Arial', 12, 'bold')
        ).pack()
        
        ttk.Label(
            header_frame,
            text="I campi sono sincronizzati automaticamente per evitare conflitti",
            font=('Arial', 9),
            foreground='blue'
        ).pack(pady=(0, 10))
        
        # Container barriere
        barriers_frame = ttk.Frame(frame)
        barriers_frame.pack(fill='both', expand=True, padx=10)
        
        # Barriera Cedola (ENHANCED)
        self.coupon_barrier_frame = SmartBarrierFrame(
            barriers_frame,
            "🎯 Barriera Cedola",
            "coupon",
            self._on_barrier_changed
        )
        self.coupon_barrier_frame.pack(fill='x', pady=(0, 20))
        
        # Separatore
        ttk.Separator(barriers_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Barriera Capitale (ENHANCED)
        self.capital_barrier_frame = SmartBarrierFrame(
            barriers_frame,
            "🛡️ Barriera Capitale",
            "capital", 
            self._on_barrier_changed
        )
        self.capital_barrier_frame.pack(fill='x', pady=(0, 20))
        
        # Validazione globale
        self.global_validation_frame = ttk.LabelFrame(
            barriers_frame,
            text="Validazione Globale",
            padding=10
        )
        self.global_validation_frame.pack(fill='x', pady=10)
        
        self.global_status_label = ttk.Label(
            self.global_validation_frame,
            text="○ In attesa di configurazione...",
            foreground='gray'
        )
        self.global_status_label.pack()
        
        # Pulsante auto-fix
        self.auto_fix_button = ttk.Button(
            self.global_validation_frame,
            text="🔧 Auto-Fix Configurazione",
            command=self._auto_fix_barriers,
            state='disabled'
        )
        self.auto_fix_button.pack(pady=(5, 0))
    
    def _create_advanced_structure_tab(self, notebook):
        """Tab struttura avanzata"""
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Struttura Avanzata")
        
        # Memory feature
        memory_frame = ttk.LabelFrame(frame, text="Memory Feature", padding=10)
        memory_frame.pack(fill='x', padx=10, pady=10)
        
        self.memory_var = tk.BooleanVar()
        ttk.Checkbutton(
            memory_frame,
            text="Memory Feature (cedole accumulate)",
            variable=self.memory_var
        ).pack()
        
        # Underlying evaluation (NUOVO!)
        eval_frame = ttk.LabelFrame(frame, text="🎯 Underlying Evaluation", padding=10)
        eval_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(eval_frame, text="Metodo valutazione sottostanti:").pack(anchor='w')
        
        self.evaluation_var = tk.StringVar(value='worst_of')
        
        eval_options = [
            ('worst_of', 'Worst Of (performance peggiore)'),
            ('best_of', 'Best Of (performance migliore)'),
            ('average', 'Average (performance media)'),
            ('rainbow', 'Rainbow (contributo individuale)')
        ]
        
        for value, text in eval_options:
            ttk.Radiobutton(
                eval_frame,
                text=text,
                variable=self.evaluation_var,
                value=value
            ).pack(anchor='w', padx=20)
        
        # Info evaluation
        info_eval_frame = ttk.Frame(eval_frame)
        info_eval_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(
            info_eval_frame,
            text="ℹ️ La scelta influenza significativamente il fair value del certificato",
            foreground='blue',
            font=('Arial', 9)
        ).pack()
    
    def _create_validation_tab(self, notebook):
        """Tab validazione completa"""
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="✓ Validazione")
        
        # Validation results
        self.validation_text = tk.Text(frame, height=20, width=80)
        self.validation_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Validation controls
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(
            controls_frame,
            text="🔍 Esegui Validazione Completa",
            command=self._run_full_validation
        ).pack(side='left')
        
        ttk.Button(
            controls_frame,
            text="📋 Esporta Report Validazione",
            command=self._export_validation_report
        ).pack(side='right')
    
    def _create_bottom_buttons(self, parent):
        """Crea pulsanti bottom"""
        
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="❌ Annulla",
            command=self.destroy
        ).pack(side='right', padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="💾 Salva",
            command=self._save_certificate
        ).pack(side='right')
        
        ttk.Button(
            button_frame,
            text="🧪 Test Configurazione",
            command=self._test_configuration
        ).pack(side='left')
    
    def _on_barrier_changed(self, barrier_name: str, barrier_type: str, value: float):
        """Callback quando cambia una barriera"""
        
        # Validazione globale
        self._update_global_validation()
        
        logging.info(f"Barriera {barrier_name} cambiata: {barrier_type} = {value}%")
    
    def _update_global_validation(self):
        """Aggiorna validazione globale"""
        
        coupon_values = self.coupon_barrier_frame.get_values()
        capital_values = self.capital_barrier_frame.get_values()
        
        validation = BarrierLogicManager.validate_barrier_consistency(
            coupon_values['type'], coupon_values['value'],
            capital_values['type'], capital_values['value']
        )
        
        if validation['valid']:
            if validation['warnings']:
                status_text = f"⚠️ Configurazione valida con warning"
                status_color = 'orange'
                self.auto_fix_button.configure(state='normal')
            else:
                status_text = "✅ Configurazione valida"
                status_color = 'green'
                self.auto_fix_button.configure(state='disabled')
        else:
            status_text = f"❌ Errori: {len(validation['errors'])}"
            status_color = 'red'
            self.auto_fix_button.configure(state='normal')
        
        self.global_status_label.configure(text=status_text, foreground=status_color)
        
        # Aggiorna validation_errors per uso esterno
        self.validation_errors = validation['errors'] + validation['warnings']
    
    def _auto_fix_barriers(self):
        """Auto-fix automatico delle barriere"""
        
        coupon_values = self.coupon_barrier_frame.get_values()
        capital_values = self.capital_barrier_frame.get_values()
        
        # Logic auto-fix
        if coupon_values['type'] == 'none' and coupon_values['value'] != 0.0:
            self.coupon_barrier_frame.set_values('none', 0.0)
        
        if capital_values['type'] == 'none' and capital_values['value'] != 0.0:
            self.capital_barrier_frame.set_values('none', 0.0)
        
        # Se entrambi sono none, suggerisci configurazione tipica
        if coupon_values['type'] == 'none' and capital_values['type'] == 'none':
            result = messagebox.askyesno(
                "Auto-Fix Suggerito",
                "Configurazione tipica Express:\n\n"
                "• Barriera Cedola: protected 70%\n"
                "• Barriera Capitale: protected 60%\n\n"
                "Applicare questa configurazione?"
            )
            
            if result:
                self.coupon_barrier_frame.set_values('protected', 70.0)
                self.capital_barrier_frame.set_values('protected', 60.0)
        
        messagebox.showinfo("Auto-Fix", "Auto-fix completato!")
    
    def _run_full_validation(self):
        """Esegui validazione completa"""
        
        self.validation_text.delete(1.0, tk.END)
        
        validation_report = "🔍 VALIDAZIONE COMPLETA CERTIFICATO\n"
        validation_report += "=" * 50 + "\n\n"
        
        # Validazione barriere
        coupon_values = self.coupon_barrier_frame.get_values()
        capital_values = self.capital_barrier_frame.get_values()
        
        barrier_validation = BarrierLogicManager.validate_barrier_consistency(
            coupon_values['type'], coupon_values['value'],
            capital_values['type'], capital_values['value']
        )
        
        validation_report += "🛡️ BARRIERE:\n"
        if barrier_validation['valid']:
            validation_report += "✅ Configurazione barriere valida\n"
        else:
            validation_report += "❌ Errori nelle barriere:\n"
            for error in barrier_validation['errors']:
                validation_report += f"  • {error}\n"
        
        if barrier_validation['warnings']:
            validation_report += "⚠️ Warning:\n"
            for warning in barrier_validation['warnings']:
                validation_report += f"  • {warning}\n"
        
        validation_report += "\n"
        
        # Validazione underlying evaluation
        evaluation_type = self.evaluation_var.get()
        validation_report += f"🎯 UNDERLYING EVALUATION:\n"
        validation_report += f"✅ Metodo selezionato: {evaluation_type}\n"
        
        impact_description = {
            'worst_of': 'Fair value più conservativo (tipico Express)',
            'best_of': 'Fair value più ottimistico',
            'average': 'Fair value bilanciato',
            'rainbow': 'Fair value personalizzato'
        }
        
        validation_report += f"📊 Impatto: {impact_description[evaluation_type]}\n\n"
        
        # Memory feature
        memory_enabled = self.memory_var.get()
        validation_report += f"💭 MEMORY FEATURE:\n"
        validation_report += f"✅ Stato: {'Attivato' if memory_enabled else 'Disattivato'}\n"
        if memory_enabled:
            validation_report += "📈 Effetto: Accumulo cedole non pagate\n"
        validation_report += "\n"
        
        # Summary
        validation_report += "📋 SUMMARY:\n"
        if barrier_validation['valid'] and not barrier_validation['warnings']:
            validation_report += "✅ Certificato configurato correttamente\n"
            validation_report += "🚀 Pronto per il pricing\n"
        else:
            validation_report += "⚠️ Certificato configurato con warning\n"
            validation_report += "🔧 Raccomandato auto-fix prima del pricing\n"
        
        self.validation_text.insert(tk.END, validation_report)
    
    def _export_validation_report(self):
        """Esporta report validazione"""
        messagebox.showinfo("Export", "Funzione export da implementare")
    
    def _test_configuration(self):
        """Test configurazione con pricing rapido"""
        messagebox.showinfo("Test", "Test pricing rapido da implementare")
    
    def _save_certificate(self):
        """Salva certificato con validazione"""
        
        # Validazione finale
        self._update_global_validation()
        
        if self.validation_errors:
            result = messagebox.askyesno(
                "Errori Validazione",
                f"Trovati {len(self.validation_errors)} errori/warning:\n\n" +
                "\n".join(self.validation_errors[:3]) +
                ("\n..." if len(self.validation_errors) > 3 else "") +
                "\n\nSalvare comunque?"
            )
            
            if not result:
                return
        
        # Raccoglie dati
        certificate_data = self._collect_certificate_data()
        
        # Salva (logica da implementare)
        messagebox.showinfo("Salvato", "Certificato salvato con successo!")
        self.destroy()
    
    def _collect_certificate_data(self) -> Dict[str, Any]:
        """Raccoglie tutti i dati del certificato"""
        
        coupon_values = self.coupon_barrier_frame.get_values()
        capital_values = self.capital_barrier_frame.get_values()
        
        return {
            'coupon_barrier_type': coupon_values['type'],
            'coupon_barrier_value': coupon_values['value'],
            'capital_barrier_type': capital_values['type'],
            'capital_barrier_value': capital_values['value'],
            'memory_feature': self.memory_var.get(),
            'underlying_evaluation': self.evaluation_var.get(),
            # Altri campi...
        }
    
    def _load_data(self):
        """Carica dati esistenti se in modalità modifica"""
        
        if not self.certificate_data:
            return
        
        # Carica valori barriere
        if 'coupon_barrier_type' in self.certificate_data:
            self.coupon_barrier_frame.set_values(
                self.certificate_data['coupon_barrier_type'],
                self.certificate_data.get('coupon_barrier_value', 0.0)
            )
        
        if 'capital_barrier_type' in self.certificate_data:
            self.capital_barrier_frame.set_values(
                self.certificate_data['capital_barrier_type'],
                self.certificate_data.get('capital_barrier_value', 0.0)
            )
        
        # Carica altri valori
        if 'memory_feature' in self.certificate_data:
            self.memory_var.set(self.certificate_data['memory_feature'])
        
        if 'underlying_evaluation' in self.certificate_data:
            self.evaluation_var.set(self.certificate_data['underlying_evaluation'])
    
    def center_window(self):
        """Centra finestra"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

# ========================================
# TESTING
# ========================================

def test_barrier_fix():
    """Test del sistema fix barriere"""
    
    print("🔧 TESTING BARRIER FIX SYSTEM")
    print("=" * 50)
    
    # Test logica manager
    print("\n1. Test BarrierLogicManager:")
    
    # Test configurazioni
    for barrier_type in ['none', 'protected', 'dynamic']:
        config = BarrierLogicManager.get_barrier_config(barrier_type)
        print(f"  {barrier_type}: enabled={config['coupon_enabled']}, default={config['coupon_default']}")
    
    # Test validazione
    print("\n2. Test validazione:")
    
    test_cases = [
        ('none', 0.0, 'none', 0.0),      # OK
        ('none', 70.0, 'protected', 60.0),  # Error - none con valore
        ('protected', 70.0, 'protected', 60.0),  # OK
        ('protected', 120.0, 'protected', 60.0),  # Error - fuori range
    ]
    
    for coupon_type, coupon_val, capital_type, capital_val in test_cases:
        validation = BarrierLogicManager.validate_barrier_consistency(
            coupon_type, coupon_val, capital_type, capital_val
        )
        status = "✅" if validation['valid'] else "❌"
        print(f"  {status} {coupon_type}:{coupon_val}% / {capital_type}:{capital_val}%")
        if validation['errors']:
            print(f"    Errori: {validation['errors'][0]}")
    
    print("\n✅ Test BarrierLogicManager completato!")
    
    # Test GUI (se ambiente grafico disponibile)
    try:
        root = tk.Tk()
        root.withdraw()  # Nascondi finestra principale
        
        # Test dialog
        dialog = EnhancedCertificateDialog(root)
        print("\n🖥️ GUI Dialog creato - chiudi per continuare test")
        root.wait_window(dialog)
        
        root.destroy()
        print("✅ Test GUI completato!")
        
    except Exception as e:
        print(f"⚠️ Test GUI skippato: {e}")
    
    return True

if __name__ == "__main__":
    """Test standalone"""
    test_barrier_fix()
