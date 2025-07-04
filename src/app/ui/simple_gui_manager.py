# ==========================================================
# RIEPILOGO CONTENUTO FILE:
# - Classi GUI: EnhancedCertificateDialog
# ==========================================================
# - (Funzioni e metodi da elencare quando il file sarà popolato)

# ========================================
# SIMPLE GUI MANAGER - Interface Funzionante
# GUI semplice che funziona con il sistema esistente
# File: simple_gui_manager.py
# Timestamp : 2025-06-15 20:39:00
# Inserimento pulsante portafogli
# ========================================

"""
*** SIMPLE GUI MANAGER ***

OBIETTIVO: GUI funzionante per inserimento/modifica certificati
- Usa il sistema esistente (real_certificate_integration.py)
- Dialog di inserimento/modifica realmente funzionanti
- Analisi certificati integrata
- Gestione configurazioni JSON

USO:
1. Salva come: simple_gui_manager.py
2. Esegui: python simple_gui_manager.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Import sistema esistente
try:
    from app.utils.real_certificate_integration import (
        RealCertificateConfig, IntegratedCertificateSystem
    )
    print("✅ Import sistema esistente OK")
except ImportError as e:
    print(f"❌ Errore import: {e}")
    messagebox.showerror("Errore", f"Impossibile importare sistema: {e}")
    exit(1)

class SimpleCertificateGUI:
    """GUI semplice e funzionante per gestione certificati"""
    
    def __init__(self):
        # Sistema integrato
        self.system = IntegratedCertificateSystem()
        self.config_dir = Path("D:/Doc/File python/configs/") #DA VERIFICARE
        self.config_dir.mkdir(exist_ok=True)
        
        # File configurazioni
        self.cert_file = self.config_dir / "enhanced_certificates.json"
        if not self.cert_file.exists():
            self.cert_file = self.config_dir / "certificates1.json"  # Fallback
        
        # Carica configurazioni esistenti
        self.certificates = self._load_certificates()
        
        # Main window
        self.root = tk.Tk()
        self.root.title("Certificate Manager - GUI Semplice")
        self.root.geometry("1000x700")
        
        # Setup GUI
        self._setup_interface()
        
 
        # Carica lista iniziale
        self._refresh_certificate_list()
        
        print(f"🖥️  GUI semplice inizializzata con {len(self.certificates)} certificati")
    
    def _load_certificates(self):
        """Carica certificati esistenti"""
        
        if not self.cert_file.exists():
            return {}
        
        try:
            with open(self.cert_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Gestisce formato enhanced e basic
            certificates = {}
            for cert_id, cert_data in data.items():
                if 'base_config' in cert_data:
                    # Formato enhanced
                    certificates[cert_id] = cert_data['base_config']
                else:
                    # Formato basic
                    certificates[cert_id] = cert_data
            
            return certificates
            
        except Exception as e:
            print(f"⚠️  Errore caricamento certificati: {e}")
            return {}
    
    def _save_certificates(self):
        """*** FIX SALVATAGGIO *** - Salva certificati correttamente"""
        
        try:
            # Backup del file esistente
            if self.cert_file.exists():
                backup_file = self.cert_file.with_suffix('.backup.json')
                import shutil
                shutil.copy2(self.cert_file, backup_file)
            
            # Salva con formato corretto
            with open(self.cert_file, 'w', encoding='utf-8') as f:
                json.dump(self.certificates, f, indent=2, default=str, ensure_ascii=False)
            
            print(f"✅ Certificati salvati in {self.cert_file}")
            
            # Verifica salvataggio
            with open(self.cert_file, 'r', encoding='utf-8') as f:
                test_load = json.load(f)
            print(f"✅ Verifica salvataggio: {len(test_load)} certificati")
            
        except Exception as e:
            print(f"❌ Errore salvataggio: {e}")
            messagebox.showerror("Errore", f"Impossibile salvare: {e}")
            # Ripristina backup se esiste
            backup_file = self.cert_file.with_suffix('.backup.json')
            if backup_file.exists():
                import shutil
                shutil.copy2(backup_file, self.cert_file)
                print("🔄 Ripristinato backup")
    
    def _setup_interface(self):
        """Setup interface principale"""
        
        # Menu bar
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nuovo Certificato", command=self._new_certificate)
        file_menu.add_command(label="Importa da File", command=self._import_from_file)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.root.quit)
        
        # Actions menu
        actions_menu = tk.Menu(menubar, tearoff=0)
        actions_menu.add_command(label="Analizza Selezionato", command=self._analyze_selected)
        actions_menu.add_command(label="Calcola Date Automatico", command=self._auto_calculate_dates)
        
        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Azioni", menu=actions_menu)
        
        self.root.config(menu=menubar)
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Lista certificati
        left_frame = ttk.LabelFrame(main_frame, text="Certificati")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Treeview
        columns = ('ISIN', 'Nome', 'Tipo', 'Emittente', 'Scadenza')
        self.tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right panel - Dettagli e azioni
        right_frame = ttk.LabelFrame(main_frame, text="Dettagli e Azioni")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        # Dettagli area
        details_frame = ttk.Frame(right_frame)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.details_text = tk.Text(details_frame, height=25, width=50, wrap=tk.WORD)
        details_scroll = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pulsanti azioni
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Nuovo Certificato", 
                  command=self._new_certificate).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Modifica Selezionato", 
                  command=self._edit_selected).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Analizza Certificato", 
                  command=self._analyze_selected).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Calcola Date Auto", 
                  command=self._auto_calculate_dates).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Elimina Selezionato", 
                  command=self._delete_selected).pack(fill=tk.X, pady=2)
        
        # Bind eventi
        self.tree.bind('<<TreeviewSelect>>', self._on_certificate_select)
        self.tree.bind('<Double-1>', self._edit_selected)  # Double click per modifica
    
    def _refresh_certificate_list(self):
        """Aggiorna lista certificati"""
        
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add certificates
        for cert_id, cert_data in self.certificates.items():
            try:
                name = cert_data.get('name', 'N/A')[:30]
                cert_type = cert_data.get('certificate_type', 'N/A')
                issuer = cert_data.get('issuer', 'N/A')[:20]
                
                maturity = cert_data.get('maturity_date', 'N/A')
                if isinstance(maturity, str) and maturity != 'N/A':
                    try:
                        maturity = datetime.fromisoformat(maturity).strftime('%Y-%m-%d')
                    except:
                        pass
                
                self.tree.insert('', tk.END, values=(
                    cert_id, name, cert_type, issuer, maturity
                ))
            except Exception as e:
                print(f"⚠️  Errore visualizzazione {cert_id}: {e}")
    
    def _on_certificate_select(self, event):
        """Gestisce selezione certificato"""
        
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        cert_id = item['values'][0]
        
        if cert_id in self.certificates:
            self._display_certificate_details(cert_id)
    
    def _display_certificate_details(self, cert_id):
        """Mostra dettagli certificato"""
        
        cert_data = self.certificates[cert_id]
        
        # Formatta dettagli
        details = f"""DETTAGLI CERTIFICATO
{'='*50}

INFORMAZIONI BASE:
ISIN: {cert_data.get('isin', 'N/A')}
Nome: {cert_data.get('name', 'N/A')}
Tipo: {cert_data.get('certificate_type', 'N/A')}
Emittente: {cert_data.get('issuer', 'N/A')}
Valuta: {cert_data.get('currency', 'EUR')}

DATE:
Emissione: {cert_data.get('issue_date', 'N/A')}
Scadenza: {cert_data.get('maturity_date', 'N/A')}

PARAMETRI FINANZIARI:
Nominale: €{cert_data.get('notional', 0):,.2f}
Memory Feature: {cert_data.get('memory_feature', False)}
Risk-Free Rate: {cert_data.get('risk_free_rate', 0):.2%}

SOTTOSTANTI:
{chr(10).join(f"  - {asset}" for asset in cert_data.get('underlying_assets', []))}

CEDOLE:
Numero Cedole: {len(cert_data.get('coupon_dates', []))}
Rate Cedole: {cert_data.get('coupon_rates', [])[:3]}{'...' if len(cert_data.get('coupon_rates', [])) > 3 else ''}

BARRIERE:
{self._format_barriers(cert_data.get('barrier_levels', {}))}

DATI MERCATO:
Current Spots: {cert_data.get('current_spots', 'N/A')}
Volatilità: {cert_data.get('volatilities', 'N/A')}

AUTOCALL:
Livelli: {cert_data.get('autocall_levels', [])[:3]}{'...' if len(cert_data.get('autocall_levels', [])) > 3 else ''}
"""
        
        # Mostra dettagli
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
    
    def _format_barriers(self, barriers):
        """Formatta barriere per display"""
        if not barriers:
            return "N/A"
        
        formatted = []
        for key, value in barriers.items():
            formatted.append(f"{key}: {value:.1%}")
        
        return ", ".join(formatted)
    
    def _new_certificate(self):
        """Apre dialog nuovo certificato"""
        dialog = CertificateDialog(self.root, "Nuovo Certificato")
        
        if dialog.result:
            cert_data = dialog.result
            cert_id = cert_data['isin']
            
            # Verifica unicità ISIN
            if cert_id in self.certificates:
                if not messagebox.askyesno("ISIN Esistente", 
                                         f"ISIN {cert_id} già esistente. Sovrascrivere?"):
                    return
            
            # Salva certificato
            self.certificates[cert_id] = cert_data
            self._save_certificates()
            self._refresh_certificate_list()
            
            messagebox.showinfo("Successo", f"Certificato {cert_id} creato con successo!")
    
    def _edit_selected(self, event=None):
        """Modifica certificato selezionato"""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da modificare")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]
        cert_data = self.certificates[cert_id]
        
        # Apre dialog con dati esistenti
        dialog = CertificateDialog(self.root, f"Modifica {cert_id}", cert_data)
        
        if dialog.result:
            # Aggiorna certificato
            self.certificates[cert_id] = dialog.result
            self._save_certificates()
            self._refresh_certificate_list()
            self._display_certificate_details(cert_id)
            
            messagebox.showinfo("Successo", f"Certificato {cert_id} aggiornato!")
    
    def _analyze_selected(self):
        """Analizza certificato selezionato"""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da analizzare")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]
        cert_data = self.certificates[cert_id]
        
        # Mostra dialog di attesa
        progress_dialog = ProgressDialog(self.root, "Analisi in corso...")
        
        def run_analysis():
            try:
                # Converte in RealCertificateConfig
                config = self._dict_to_real_config(cert_data.copy())
                
                # Esegue analisi
                certificate, results = self.system.process_real_certificate(
                    config, create_excel_report=True, run_full_analysis=True
                )
                
                # Chiude dialog progresso
                progress_dialog.close()
                
                # Mostra risultati
                self._show_analysis_results(cert_id, results)
                
            except Exception as e:
                progress_dialog.close()
                messagebox.showerror("Errore Analisi", f"Errore durante l'analisi:\n{e}")
        
        # Esegue in thread separato
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
    
    def _show_analysis_results(self, cert_id, results):
        """Mostra risultati analisi"""
        
        if not results:
            messagebox.showinfo("Analisi Completata", f"Analisi di {cert_id} completata senza risultati.")
            return
        
        # Formatta risultati
        result_text = f"RISULTATI ANALISI - {cert_id}\n{'='*50}\n\n"
        
        # Fair Value
        if 'fair_value' in results:
            fv = results['fair_value']
            result_text += "FAIR VALUE:\n"
            result_text += f"  Fair Value: €{fv.get('fair_value', 0):,.2f}\n"
            result_text += f"  Expected Return: {fv.get('expected_return', 0):.2%}\n"
            result_text += f"  Annualized Return: {fv.get('annualized_return', 0):.2%}\n\n"
        
        # Risk Metrics
        if 'risk_metrics' in results:
            risk = results['risk_metrics']
            result_text += "RISK METRICS:\n"
            if hasattr(risk, 'var_95'):
                result_text += f"  VaR 95%: {risk.var_95:.2%}\n"
                result_text += f"  VaR 99%: {risk.var_99:.2%}\n"
                result_text += f"  Volatilità: {risk.volatility:.2%}\n"
                result_text += f"  Sharpe Ratio: {risk.sharpe_ratio:.3f}\n\n"
        
        # Compliance
        if 'compliance' in results:
            comp = results['compliance']
            result_text += "COMPLIANCE:\n"
            result_text += f"  Score: {comp.get('score', 0):.1f}/100\n"
            result_text += f"  Compliant: {comp.get('compliant', False)}\n\n"
        
        # Mostra in dialog
        ResultsDialog(self.root, "Risultati Analisi", result_text)
    
    def _auto_calculate_dates(self):
        """Calcola automaticamente date cedole per certificato selezionato"""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]
        
        # Dialog per parametri calcolo automatico
        dialog = AutoDateCalculatorDialog(self.root, cert_id, self.certificates[cert_id])
        
        if dialog.result:
            # Aggiorna certificato con date calcolate
            self.certificates[cert_id].update(dialog.result)
            self._save_certificates()
            self._refresh_certificate_list()
            self._display_certificate_details(cert_id)
            
            messagebox.showinfo("Successo", f"Date calcolate automaticamente per {cert_id}!")
    
    def _delete_selected(self):
        """Elimina certificato selezionato"""
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato da eliminare")
            return
        
        cert_id = self.tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Conferma Eliminazione", f"Eliminare il certificato {cert_id}?"):
            del self.certificates[cert_id]
            self._save_certificates()
            self._refresh_certificate_list()
            self.details_text.delete(1.0, tk.END)
            
            messagebox.showinfo("Successo", f"Certificato {cert_id} eliminato")
    
    def _import_from_file(self):
        """Importa certificati da file JSON"""
        
        file_path = filedialog.askopenfilename(
            title="Importa Certificati",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                count = 0
                for cert_id, cert_data in imported_data.items():
                    if cert_id not in self.certificates or messagebox.askyesno(
                        "ISIN Esistente", f"ISIN {cert_id} già esistente. Sovrascrivere?"
                    ):
                        # Gestisce formato enhanced
                        if 'base_config' in cert_data:
                            self.certificates[cert_id] = cert_data['base_config']
                        else:
                            self.certificates[cert_id] = cert_data
                        count += 1
                
                self._save_certificates()
                self._refresh_certificate_list()
                
                messagebox.showinfo("Import Completato", f"Importati {count} certificati")
                
            except Exception as e:
                messagebox.showerror("Errore Import", f"Errore durante l'import:\n{e}")
    
    def _dict_to_real_config(self, config_dict):
        """Converte dict in RealCertificateConfig"""
        
        # Fix date
        for date_field in ['issue_date', 'maturity_date']:
            if isinstance(config_dict.get(date_field), str):
                config_dict[date_field] = datetime.fromisoformat(config_dict[date_field])
        
        # Fix date lists
        for date_list_field in ['coupon_dates', 'autocall_dates']:
            if config_dict.get(date_list_field):
                config_dict[date_list_field] = [
                    datetime.fromisoformat(date) if isinstance(date, str) else date
                    for date in config_dict[date_list_field]
                ]
        
        # Fix correlations
        if config_dict.get('correlations') and isinstance(config_dict['correlations'], list):
            import numpy as np
            config_dict['correlations'] = np.array(config_dict['correlations'])
        
        return RealCertificateConfig(**config_dict)
    
    def run(self):
        """Avvia GUI"""
        self.root.mainloop()


# ========================================
# DIALOG CLASSES
# ========================================

class EnhancedCertificateDialog:
    """*** VERSIONE AVANZATA *** - Dialog con tipi certificato e campi dinamici"""
    
    def __init__(self, parent, title, existing_data=None):
        self.result = None
        self.existing_data = existing_data
        
        # Dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("700x800")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Certificate types con parametri specifici
        self.certificate_types = {
            'cash_collect': {
                'name': 'Cash Collect / Memory',
                'required_params': ['coupon_barrier', 'memory_feature', 'autocall'],
                'description': 'Certificato con cedole condizionali e memoria'
            },
            'express': {
                'name': 'Express / Autocallable',
                'required_params': ['autocall', 'capital_protection'],
                'description': 'Certificato con rimborso anticipato automatico'
            },
            'phoenix': {
                'name': 'Phoenix',
                'required_params': ['coupon_barrier', 'capital_barrier', 'memory_feature'],
                'description': 'Certificato con barriere multiple'
            },
            'barrier': {
                'name': 'Barrier Certificate',
                'required_params': ['capital_barrier', 'capital_protection'],
                'description': 'Certificato con barriera capitale'
            },
            'capital_protected': {
                'name': 'Capitale Protetto',
                'required_params': ['protection_level', 'participation_rate'],
                'description': 'Certificato con protezione capitale garantita'
            },
            'bonus': {
                'name': 'Bonus Certificate',
                'required_params': ['bonus_level', 'capital_barrier'],
                'description': 'Certificato con bonus se barriera non toccata'
            },
            'altro': {
                'name': 'Altro (Configurazione Manuale)',
                'required_params': [],
                'description': 'Per configurazioni speciali non standard'
            }
        }
        
        # Setup form
        self._setup_form()
    
    def _setup_form(self):
        """Setup form avanzato con campi dinamici"""
        
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Scroll frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form fields
        self.fields = {}
        self.dynamic_frames = {}
        
        # ========================================
        # SEZIONE 1: INFORMAZIONI BASE
        # ========================================
        
        basic_frame = ttk.LabelFrame(self.scrollable_frame, text="Informazioni Base")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        basic_fields = [
            ("ISIN", "isin", self.existing_data.get('isin', '') if self.existing_data else ''),
            ("Nome", "name", self.existing_data.get('name', '') if self.existing_data else ''),
            ("Emittente", "issuer", self.existing_data.get('issuer', '') if self.existing_data else ''),
            ("Nominale", "notional", str(self.existing_data.get('notional', 1000)) if self.existing_data else '1000'),
            ("Valuta", "currency", self.existing_data.get('currency', 'EUR') if self.existing_data else 'EUR')
        ]
        
        for label, key, default_value in basic_fields:
            frame = ttk.Frame(basic_frame)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            ttk.Label(frame, text=f"{label}:", width=15).pack(side=tk.LEFT)
            entry = ttk.Entry(frame, width=40)
            entry.pack(side=tk.LEFT, padx=(5, 0))
            entry.insert(0, default_value)
            
            self.fields[key] = entry
        
        # ========================================
        # SEZIONE 2: TIPO CERTIFICATO (DINAMICO)
        # ========================================
        
        type_frame = ttk.LabelFrame(self.scrollable_frame, text="Tipo Certificato")
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Menu a tendina tipo
        type_inner = ttk.Frame(type_frame)
        type_inner.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(type_inner, text="Tipo Certificato:", width=15).pack(side=tk.LEFT)
        
        self.cert_type_var = tk.StringVar()
        current_type = self.existing_data.get('certificate_type', 'cash_collect') if self.existing_data else 'cash_collect'
        self.cert_type_var.set(current_type)
        
        type_values = list(self.certificate_types.keys())
        self.type_combo = ttk.Combobox(type_inner, textvariable=self.cert_type_var, 
                                      values=type_values, width=25)
        self.type_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.type_combo.bind('<<ComboboxSelected>>', self._on_type_change)
        
        # Descrizione tipo
        self.type_description = ttk.Label(type_frame, text="", font=("Arial", 9, "italic"))
        self.type_description.pack(padx=10, pady=(0, 10))
        
        # ========================================
        # SEZIONE 3: PARAMETRI DINAMICI
        # ========================================
        
        self.dynamic_params_frame = ttk.LabelFrame(self.scrollable_frame, text="Parametri Specifici")
        self.dynamic_params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ========================================
        # SEZIONE 4: DATE
        # ========================================
        
        date_frame = ttk.LabelFrame(self.scrollable_frame, text="Date")
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        date_fields = [
            ("Data Emissione", "issue_date", self._format_date(self.existing_data.get('issue_date', '2024-01-15'))),
            ("Data Scadenza", "maturity_date", self._format_date(self.existing_data.get('maturity_date', '2029-01-15')))
        ]
        
        for label, key, default_value in date_fields:
            frame = ttk.Frame(date_frame)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            ttk.Label(frame, text=f"{label}:", width=15).pack(side=tk.LEFT)
            entry = ttk.Entry(frame, width=40)
            entry.pack(side=tk.LEFT, padx=(5, 0))
            entry.insert(0, default_value)
            self.fields[key] = entry
        
        # ========================================
        # SEZIONE 5: UNDERLYING ASSETS
        # ========================================
        
        assets_frame = ttk.LabelFrame(self.scrollable_frame, text="Sottostanti")
        assets_frame.pack(fill=tk.X, pady=(0, 10))
        
        assets_inner = ttk.Frame(assets_frame)
        assets_inner.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(assets_inner, text="Assets (separati da virgola):").pack(anchor=tk.W)
        self.assets_entry = tk.Text(assets_inner, height=3, width=60)
        self.assets_entry.pack(fill=tk.X, pady=(5, 0))
        
        if self.existing_data and self.existing_data.get('underlying_assets'):
            assets_text = ', '.join(self.existing_data['underlying_assets'])
            self.assets_entry.insert(1.0, assets_text)
        
        # ========================================
        # SEZIONE 6: OPZIONI GENERALI
        # ========================================
        
        options_frame = ttk.LabelFrame(self.scrollable_frame, text="Opzioni Generali")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Risk-free rate
        rf_frame = ttk.Frame(options_frame)
        rf_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(rf_frame, text="Risk-Free Rate (%):", width=20).pack(side=tk.LEFT)
        self.rf_entry = ttk.Entry(rf_frame, width=10)
        self.rf_entry.pack(side=tk.LEFT, padx=(5, 0))
        rf_value = self.existing_data.get('risk_free_rate', 0.035) if self.existing_data else 0.035
        self.rf_entry.insert(0, f"{rf_value*100:.1f}")
        
        # ========================================
        # BUTTONS
        # ========================================
        
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Annulla", 
                  command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Salva Certificato", 
                  command=self._save).pack(side=tk.RIGHT)
        
        # Pack scrollable elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Inizializza campi dinamici
        self._on_type_change()
    
    def _format_date(self, date_value):
        """Formatta data per display"""
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        elif isinstance(date_value, str) and date_value:
            try:
                dt = datetime.fromisoformat(date_value)
                return dt.strftime('%Y-%m-%d')
            except:
                return date_value
        return date_value or '2024-01-15'
    
    def _on_type_change(self, event=None):
        """*** CAMPI DINAMICI *** - Gestisce cambio tipo certificato"""
        
        cert_type = self.cert_type_var.get()
        
        # Aggiorna descrizione
        if cert_type in self.certificate_types:
            type_info = self.certificate_types[cert_type]
            self.type_description.config(text=type_info['description'])
        
        # Pulisci frame dinamico
        for widget in self.dynamic_params_frame.winfo_children():
            widget.destroy()
        
        # Crea campi specifici per tipo
        if cert_type == 'cash_collect':
            self._create_cash_collect_params()
        elif cert_type == 'express':
            self._create_express_params()
        elif cert_type == 'phoenix':
            self._create_phoenix_params()
        elif cert_type == 'barrier':
            self._create_barrier_params()
        elif cert_type == 'capital_protected':
            self._create_capital_protected_params()
        elif cert_type == 'bonus':
            self._create_bonus_params()
        elif cert_type == 'altro':
            self._create_manual_config_params()
    
    def _create_cash_collect_params(self):
        """Parametri specifici Cash Collect"""
        
        # Memory feature
        memory_frame = ttk.Frame(self.dynamic_params_frame)
        memory_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.memory_var = tk.BooleanVar()
        memory_val = self.existing_data.get('memory_feature', True) if self.existing_data else True
        self.memory_var.set(memory_val)
        
        ttk.Checkbutton(memory_frame, text="Memory Feature (cedole accumulate)", 
                       variable=self.memory_var).pack(anchor=tk.W)
        
        # Coupon barrier
        cb_frame = ttk.Frame(self.dynamic_params_frame)
        cb_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(cb_frame, text="Barriera Cedola (%):", width=20).pack(side=tk.LEFT)
        self.coupon_barrier_entry = ttk.Entry(cb_frame, width=10)
        self.coupon_barrier_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        cb_val = self.existing_data.get('barrier_levels', {}).get('coupon', 0.70) if self.existing_data else 0.70
        self.coupon_barrier_entry.insert(0, f"{cb_val*100:.0f}")
        
        # Capital barrier
        cap_frame = ttk.Frame(self.dynamic_params_frame)
        cap_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(cap_frame, text="Barriera Capitale (%):", width=20).pack(side=tk.LEFT)
        self.capital_barrier_entry = ttk.Entry(cap_frame, width=10)
        self.capital_barrier_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        cap_val = self.existing_data.get('barrier_levels', {}).get('capital', 0.65) if self.existing_data else 0.65
        self.capital_barrier_entry.insert(0, f"{cap_val*100:.0f}")
        
        # Autocall
        self._create_autocall_params()
        
        # Cedole
        self._create_coupon_params()
    
    def _create_express_params(self):
        """Parametri specifici Express"""
        
        # Capital protection
        prot_frame = ttk.Frame(self.dynamic_params_frame)
        prot_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(prot_frame, text="Protezione Capitale:").pack(anchor=tk.W)
        
        self.capital_protection_var = tk.StringVar()
        prot_val = self.existing_data.get('capital_protection', 'conditional') if self.existing_data else 'conditional'
        self.capital_protection_var.set(prot_val)
        
        prot_options = [
            ('full', 'Protezione Integrale'),
            ('conditional', 'Protezione Condizionale (con barriera)'),
            ('partial', 'Protezione Parziale')
        ]
        
        for value, text in prot_options:
            ttk.Radiobutton(prot_frame, text=text, variable=self.capital_protection_var, 
                           value=value).pack(anchor=tk.W, padx=20)
        
        # Barriera capitale (se protezione condizionale)
        barrier_frame = ttk.Frame(self.dynamic_params_frame)
        barrier_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(barrier_frame, text="Barriera Capitale (%):", width=20).pack(side=tk.LEFT)
        self.capital_barrier_entry = ttk.Entry(barrier_frame, width=10)
        self.capital_barrier_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        cap_val = self.existing_data.get('barrier_levels', {}).get('capital', 0.65) if self.existing_data else 0.65
        self.capital_barrier_entry.insert(0, f"{cap_val*100:.0f}")
        
        # Autocall
        self._create_autocall_params()
        
        # Cedole
        self._create_coupon_params()
    
    def _create_phoenix_params(self):
        """Parametri specifici Phoenix"""
        
        # Memory feature
        memory_frame = ttk.Frame(self.dynamic_params_frame)
        memory_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.memory_var = tk.BooleanVar()
        memory_val = self.existing_data.get('memory_feature', True) if self.existing_data else True
        self.memory_var.set(memory_val)
        
        ttk.Checkbutton(memory_frame, text="Memory Feature", 
                       variable=self.memory_var).pack(anchor=tk.W)
        
        # Barriere multiple
        barriers_info = ttk.Label(self.dynamic_params_frame, 
                                 text="Phoenix tipicamente ha barriere separate per cedole e capitale:",
                                 font=("Arial", 9, "italic"))
        barriers_info.pack(padx=10, pady=5)
        
        # Coupon barrier
        cb_frame = ttk.Frame(self.dynamic_params_frame)
        cb_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(cb_frame, text="Barriera Cedola (%):", width=20).pack(side=tk.LEFT)
        self.coupon_barrier_entry = ttk.Entry(cb_frame, width=10)
        self.coupon_barrier_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        cb_val = self.existing_data.get('barrier_levels', {}).get('coupon', 0.70) if self.existing_data else 0.70
        self.coupon_barrier_entry.insert(0, f"{cb_val*100:.0f}")
        
        # Capital barrier
        cap_frame = ttk.Frame(self.dynamic_params_frame)
        cap_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(cap_frame, text="Barriera Capitale (%):", width=20).pack(side=tk.LEFT)
        self.capital_barrier_entry = ttk.Entry(cap_frame, width=10)
        self.capital_barrier_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        cap_val = self.existing_data.get('barrier_levels', {}).get('capital', 0.60) if self.existing_data else 0.60
        self.capital_barrier_entry.insert(0, f"{cap_val*100:.0f}")
        
        # Cedole
        self._create_coupon_params()
    
    def _create_barrier_params(self):
        """Parametri specifici Barrier Certificate"""
        
        # Tipo barriera
        barrier_type_frame = ttk.Frame(self.dynamic_params_frame)
        barrier_type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(barrier_type_frame, text="Tipo Barriera:").pack(anchor=tk.W)
        
        self.barrier_type_var = tk.StringVar()
        barrier_type_val = self.existing_data.get('barrier_type', 'european') if self.existing_data else 'european'
        self.barrier_type_var.set(barrier_type_val)
        
        barrier_options = [
            ('european', 'Europea (solo a scadenza)'),
            ('american', 'Americana (continuous monitoring)'),
            ('discrete', 'Discreta (date specifiche)')
        ]
        
        for value, text in barrier_options:
            ttk.Radiobutton(barrier_type_frame, text=text, variable=self.barrier_type_var, 
                           value=value).pack(anchor=tk.W, padx=20)
        
        # Livello barriera
        level_frame = ttk.Frame(self.dynamic_params_frame)
        level_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(level_frame, text="Livello Barriera (%):", width=20).pack(side=tk.LEFT)
        self.barrier_level_entry = ttk.Entry(level_frame, width=10)
        self.barrier_level_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        level_val = self.existing_data.get('barrier_levels', {}).get('main', 0.75) if self.existing_data else 0.75
        self.barrier_level_entry.insert(0, f"{level_val*100:.0f}")
        
        # Cedole
        self._create_coupon_params()
    
    def _create_capital_protected_params(self):
        """Parametri specifici Capitale Protetto"""
        
        # Livello protezione
        prot_frame = ttk.Frame(self.dynamic_params_frame)
        prot_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(prot_frame, text="Protezione Capitale (%):", width=20).pack(side=tk.LEFT)
        self.protection_level_entry = ttk.Entry(prot_frame, width=10)
        self.protection_level_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        prot_val = self.existing_data.get('protection_level', 1.0) if self.existing_data else 1.0
        self.protection_level_entry.insert(0, f"{prot_val*100:.0f}")
        
        # Participation rate
        part_frame = ttk.Frame(self.dynamic_params_frame)
        part_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(part_frame, text="Participation Rate (%):", width=20).pack(side=tk.LEFT)
        self.participation_rate_entry = ttk.Entry(part_frame, width=10)
        self.participation_rate_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        part_val = self.existing_data.get('participation_rate', 1.0) if self.existing_data else 1.0
        self.participation_rate_entry.insert(0, f"{part_val*100:.0f}")
        
        # Cap (opzionale)
        cap_frame = ttk.Frame(self.dynamic_params_frame)
        cap_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(cap_frame, text="Cap (%, opzionale):", width=20).pack(side=tk.LEFT)
        self.cap_entry = ttk.Entry(cap_frame, width=10)
        self.cap_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        cap_val = self.existing_data.get('cap_level', '') if self.existing_data else ''
        self.cap_entry.insert(0, str(cap_val) if cap_val else '')
    
    def _create_bonus_params(self):
        """Parametri specifici Bonus Certificate"""
        
        # Bonus level
        bonus_frame = ttk.Frame(self.dynamic_params_frame)
        bonus_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(bonus_frame, text="Livello Bonus (%):", width=20).pack(side=tk.LEFT)
        self.bonus_level_entry = ttk.Entry(bonus_frame, width=10)
        self.bonus_level_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        bonus_val = self.existing_data.get('bonus_level', 1.20) if self.existing_data else 1.20
        self.bonus_level_entry.insert(0, f"{bonus_val*100:.0f}")
        
        # Barriera
        barrier_frame = ttk.Frame(self.dynamic_params_frame)
        barrier_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(barrier_frame, text="Barriera (%):", width=20).pack(side=tk.LEFT)
        self.capital_barrier_entry = ttk.Entry(barrier_frame, width=10)
        self.capital_barrier_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        barrier_val = self.existing_data.get('barrier_levels', {}).get('capital', 0.75) if self.existing_data else 0.75
        self.capital_barrier_entry.insert(0, f"{barrier_val*100:.0f}")
    
    def _create_manual_config_params(self):
        """Parametri per configurazione manuale"""
        
        info_text = """CONFIGURAZIONE MANUALE
        
Per certificati con strutture non standard:

1. Compila i campi base (ISIN, nome, date, sottostanti)
2. Salva il certificato con parametri minimi
3. Modifica manualmente il file JSON per parametri avanzati
4. Ricarica nella GUI per verificare

Parametri avanzati modificabili nel JSON:
- Barriere custom con date specifiche
- Cedole con rates variabili nel tempo  
- Autocall levels dinamici
- Correlazioni custom tra sottostanti
- Volatilità variabile nel tempo

File di configurazione: D:/Doc/File python/configs/
        """
        
        info_label = ttk.Label(self.dynamic_params_frame, text=info_text, 
                              font=("Arial", 9), justify=tk.LEFT)
        info_label.pack(padx=10, pady=10)
        
        # Checkbox per conferma
        self.manual_confirm_var = tk.BooleanVar()
        ttk.Checkbutton(self.dynamic_params_frame, 
                       text="Confermo di voler procedere con configurazione manuale",
                       variable=self.manual_confirm_var).pack(padx=10, pady=5)
    
    def _create_autocall_params(self):
        """Parametri autocall comuni"""
        
        # Autocall feature
        autocall_frame = ttk.Frame(self.dynamic_params_frame)
        autocall_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.autocall_var = tk.BooleanVar()
        autocall_val = self.existing_data.get('has_autocall', True) if self.existing_data else True
        self.autocall_var.set(autocall_val)
        
        ttk.Checkbutton(autocall_frame, text="Autocallable (rimborso anticipato automatico)", 
                       variable=self.autocall_var).pack(anchor=tk.W)
        
        # Autocall level
        ac_level_frame = ttk.Frame(self.dynamic_params_frame)
        ac_level_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(ac_level_frame, text="Livello Autocall (%):", width=20).pack(side=tk.LEFT)
        self.autocall_level_entry = ttk.Entry(ac_level_frame, width=10)
        self.autocall_level_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Prendi primo livello se esiste
        ac_levels = self.existing_data.get('autocall_levels', [1.0]) if self.existing_data else [1.0]
        ac_val = ac_levels[0] if ac_levels else 1.0
        self.autocall_level_entry.insert(0, f"{ac_val*100:.0f}")
        
        # Tipo autocall levels
        ac_type_frame = ttk.Frame(self.dynamic_params_frame)
        ac_type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ac_type_frame, text="Livelli Autocall:").pack(anchor=tk.W)
        
        self.autocall_type_var = tk.StringVar()
        ac_type_val = self.existing_data.get('autocall_type', 'fixed') if self.existing_data else 'fixed'
        self.autocall_type_var.set(ac_type_val)
        
        ac_type_options = [
            ('fixed', 'Fissi (stesso livello per tutte le date)'),
            ('decreasing', 'Decrescenti nel tempo'),
            ('custom', 'Personalizzati (configurazione manuale)')
        ]
        
        for value, text in ac_type_options:
            ttk.Radiobutton(ac_type_frame, text=text, variable=self.autocall_type_var, 
                           value=value).pack(anchor=tk.W, padx=20)
    
    def _create_coupon_params(self):
        """Parametri cedole comuni"""
        
        # Info cedole
        coupon_info_frame = ttk.Frame(self.dynamic_params_frame)
        coupon_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(coupon_info_frame, text="CONFIGURAZIONE CEDOLE", 
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Opzioni calcolo
        calc_frame = ttk.Frame(self.dynamic_params_frame)
        calc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.coupon_calc_var = tk.StringVar()
        calc_val = self.existing_data.get('coupon_calculation', 'auto') if self.existing_data else 'auto'
        self.coupon_calc_var.set(calc_val)
        
        calc_options = [
            ('auto', 'Calcolo automatico (consigliato)'),
            ('manual', 'Configurazione manuale')
        ]
        
        for value, text in calc_options:
            ttk.Radiobutton(calc_frame, text=text, variable=self.coupon_calc_var, 
                           value=value).pack(anchor=tk.W)
        
        # Parametri auto
        auto_frame = ttk.Frame(self.dynamic_params_frame)
        auto_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Frequenza
        freq_sub_frame = ttk.Frame(auto_frame)
        freq_sub_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(freq_sub_frame, text="Frequenza:", width=15).pack(side=tk.LEFT)
        
        self.frequency_var = tk.StringVar()
        freq_val = self.existing_data.get('coupon_frequency', 'Q') if self.existing_data else 'Q'
        self.frequency_var.set(freq_val)
        
        freq_combo = ttk.Combobox(freq_sub_frame, textvariable=self.frequency_var, 
                                 values=['M', 'Q', 'S', 'A'], width=10)
        freq_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(freq_sub_frame, text="(M=Mensile, Q=Trimestrale, S=Semestrale, A=Annuale)", 
                 font=("Arial", 8)).pack(side=tk.LEFT, padx=(10, 0))
        
        # Tasso annuale
        rate_sub_frame = ttk.Frame(auto_frame)
        rate_sub_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(rate_sub_frame, text="Tasso Annuale (%):", width=15).pack(side=tk.LEFT)
        self.annual_rate_entry = ttk.Entry(rate_sub_frame, width=10)
        self.annual_rate_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Calcola rate medio esistente se disponibile
        existing_rates = self.existing_data.get('coupon_rates', []) if self.existing_data else []
        if existing_rates:
            avg_rate = sum(existing_rates) / len(existing_rates)
            # Converti a tasso annuale approssimativo
            freq_multiplier = {'M': 12, 'Q': 4, 'S': 2, 'A': 1}.get(freq_val, 4)
            annual_rate = avg_rate * freq_multiplier * 100
        else:
            annual_rate = 8.0  # Default 8%
        
        self.annual_rate_entry.insert(0, f"{annual_rate:.1f}")
    
    def _save(self):
        """*** SALVATAGGIO AVANZATO *** con parametri specifici per tipo"""
        
        try:
            # Validazione base
            required_fields = ['isin', 'name', 'notional', 'issue_date', 'maturity_date']
            
            for field in required_fields:
                if not self.fields[field].get().strip():
                    messagebox.showerror("Errore", f"Campo {field} obbligatorio")
                    return
            
            # Parse assets
            assets_text = self.assets_entry.get(1.0, tk.END).strip()
            if not assets_text:
                messagebox.showerror("Errore", "Almeno un underlying asset richiesto")
                return
            
            underlying_assets = [asset.strip() for asset in assets_text.split(',')]
            
            # Certificato base
            cert_data = {
                'isin': self.fields['isin'].get().strip().upper(),
                'name': self.fields['name'].get().strip(),
                'certificate_type': self.cert_type_var.get(),
                'issuer': self.fields['issuer'].get().strip(),
                'notional': float(self.fields['notional'].get()),
                'currency': self.fields['currency'].get().strip().upper(),
                'issue_date': self.fields['issue_date'].get().strip(),
                'maturity_date': self.fields['maturity_date'].get().strip(),
                'underlying_assets': underlying_assets,
                'risk_free_rate': float(self.rf_entry.get()) / 100,
                
                # Defaults market data
                'current_spots': [100.0] * len(underlying_assets),
                'volatilities': [0.25] * len(underlying_assets),
                'correlations': self._generate_default_correlations(len(underlying_assets)),
                'dividend_yields': [0.03] * len(underlying_assets)
            }
            
            # *** PARAMETRI SPECIFICI PER TIPO ***
            cert_type = self.cert_type_var.get()
            
            if cert_type == 'cash_collect':
                cert_data.update(self._get_cash_collect_params())
            elif cert_type == 'express':
                cert_data.update(self._get_express_params())
            elif cert_type == 'phoenix':
                cert_data.update(self._get_phoenix_params())
            elif cert_type == 'barrier':
                cert_data.update(self._get_barrier_params())
            elif cert_type == 'capital_protected':
                cert_data.update(self._get_capital_protected_params())
            elif cert_type == 'bonus':
                cert_data.update(self._get_bonus_params())
            elif cert_type == 'altro':
                if not self.manual_confirm_var.get():
                    messagebox.showerror("Errore", "Conferma richiesta per configurazione manuale")
                    return
                cert_data.update(self._get_manual_params())
            
            # *** CALCOLO AUTOMATICO CEDOLE ***
            if hasattr(self, 'coupon_calc_var') and self.coupon_calc_var.get() == 'auto':
                coupon_data = self._calculate_automatic_coupons(cert_data)
                cert_data.update(coupon_data)
            
            self.result = cert_data
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore creazione certificato:\n{e}")
            import traceback
            traceback.print_exc()
    
    def _get_cash_collect_params(self):
        """Parametri Cash Collect"""
        params = {
            'memory_feature': self.memory_var.get(),
            'barrier_levels': {
                'coupon': float(self.coupon_barrier_entry.get()) / 100,
                'capital': float(self.capital_barrier_entry.get()) / 100
            }
        }
        
        if hasattr(self, 'autocall_var'):
            params['has_autocall'] = self.autocall_var.get()
            if self.autocall_var.get():
                params['autocall_type'] = self.autocall_type_var.get()
        
        return params
    
    def _get_express_params(self):
        """Parametri Express"""
        params = {
            'capital_protection': self.capital_protection_var.get(),
            'barrier_levels': {
                'capital': float(self.capital_barrier_entry.get()) / 100
            }
        }
        
        if hasattr(self, 'autocall_var'):
            params['has_autocall'] = self.autocall_var.get()
            if self.autocall_var.get():
                params['autocall_type'] = self.autocall_type_var.get()
        
        return params
    
    def _get_phoenix_params(self):
        """Parametri Phoenix"""
        return {
            'memory_feature': self.memory_var.get(),
            'barrier_levels': {
                'coupon': float(self.coupon_barrier_entry.get()) / 100,
                'capital': float(self.capital_barrier_entry.get()) / 100
            }
        }
    
    def _get_barrier_params(self):
        """Parametri Barrier"""
        return {
            'barrier_type': self.barrier_type_var.get(),
            'barrier_levels': {
                'main': float(self.barrier_level_entry.get()) / 100
            }
        }
    
    def _get_capital_protected_params(self):
        """Parametri Capitale Protetto"""
        params = {
            'protection_level': float(self.protection_level_entry.get()) / 100,
            'participation_rate': float(self.participation_rate_entry.get()) / 100
        }
        
        cap_val = self.cap_entry.get().strip()
        if cap_val:
            params['cap_level'] = float(cap_val) / 100
        
        return params
    
    def _get_bonus_params(self):
        """Parametri Bonus"""
        return {
            'bonus_level': float(self.bonus_level_entry.get()) / 100,
            'barrier_levels': {
                'capital': float(self.capital_barrier_entry.get()) / 100
            }
        }
    
    def _get_manual_params(self):
        """Parametri configurazione manuale"""
        return {
            'manual_config': True,
            'config_notes': 'Configurazione manuale - modificare JSON per parametri avanzati'
        }
    
    def _calculate_automatic_coupons(self, cert_data):
        """Calcola automaticamente cedole"""
        
        try:
            from datetime import datetime
            
            # Parse date
            issue_date = datetime.fromisoformat(cert_data['issue_date'])
            maturity_date = datetime.fromisoformat(cert_data['maturity_date'])
            
            # Parametri
            frequency = self.frequency_var.get()
            annual_rate = float(self.annual_rate_entry.get()) / 100
            
            # Calcola date
            coupon_dates = self._calculate_coupon_dates_advanced(issue_date, maturity_date, frequency)
            
            # Calcola rates
            frequency_map = {'M': 12, 'Q': 4, 'S': 2, 'A': 1}
            periods_per_year = frequency_map[frequency]
            period_rate = annual_rate / periods_per_year
            
            coupon_rates = [period_rate] * len(coupon_dates)
            
            # Autocall levels
            if hasattr(self, 'autocall_var') and self.autocall_var.get():
                autocall_level = float(self.autocall_level_entry.get()) / 100
                autocall_type = self.autocall_type_var.get()
                
                if autocall_type == 'fixed':
                    autocall_levels = [autocall_level] * len(coupon_dates)
                elif autocall_type == 'decreasing':
                    # Decrementa del 2% ogni anno
                    autocall_levels = []
                    for i, _ in enumerate(coupon_dates):
                        decrease = (i // periods_per_year) * 0.02
                        level = max(0.80, autocall_level - decrease)  # Min 80%
                        autocall_levels.append(level)
                else:
                    autocall_levels = [autocall_level] * len(coupon_dates)
            else:
                autocall_levels = [1.0] * len(coupon_dates)
            
            return {
                'coupon_dates': [d.isoformat() for d in coupon_dates],
                'coupon_rates': coupon_rates,
                'autocall_levels': autocall_levels,
                'coupon_frequency': frequency,
                'annual_coupon_rate': annual_rate
            }
            
        except Exception as e:
            print(f"Errore calcolo automatico cedole: {e}")
            return {}
    
    def _calculate_coupon_dates_advanced(self, issue_date, maturity_date, frequency):
        """Calcolo avanzato date cedole"""
        
        months_map = {'M': 1, 'Q': 3, 'S': 6, 'A': 12}
        months_inc = months_map[frequency]
        
        coupon_dates = []
        current_date = issue_date
        
        # Prima data
        next_month = current_date.month + months_inc
        next_year = current_date.year
        if next_month > 12:
            next_year += (next_month - 1) // 12
            next_month = ((next_month - 1) % 12) + 1
        
        current_date = current_date.replace(year=next_year, month=next_month)
        
        # Genera date
        while current_date < maturity_date:
            coupon_dates.append(current_date)
            
            next_month = current_date.month + months_inc
            next_year = current_date.year
            if next_month > 12:
                next_year += (next_month - 1) // 12
                next_month = ((next_month - 1) % 12) + 1
            
            try:
                current_date = current_date.replace(year=next_year, month=next_month)
            except ValueError:
                # Gestione giorni che non esistono
                import calendar
                last_day = calendar.monthrange(next_year, next_month)[1]
                current_date = current_date.replace(year=next_year, month=next_month, 
                                                  day=min(current_date.day, last_day))
        
        # Aggiungi maturity
        coupon_dates.append(maturity_date)
        
        return coupon_dates
    
    def _generate_default_correlations(self, n_assets):
        """Genera matrice correlazioni default"""
        import numpy as np
        
        # Correlazione moderata tra asset dello stesso settore
        corr_matrix = np.full((n_assets, n_assets), 0.6)
        np.fill_diagonal(corr_matrix, 1.0)
        
        return corr_matrix.tolist()
    
    def _cancel(self):
        """Annulla dialog"""
        self.result = None
        self.dialog.destroy()


# Sostituisci la chiamata alla vecchia CertificateDialog
CertificateDialog = EnhancedCertificateDialog


class ProgressDialog:
    """Dialog progresso per analisi"""
    
    def __init__(self, parent, message):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Analisi in corso")
        self.dialog.geometry("300x100")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centra dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (100 // 2)
        self.dialog.geometry(f"300x100+{x}+{y}")
        
        # Message
        ttk.Label(self.dialog, text=message, font=("Arial", 12)).pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill=tk.X)
        self.progress.start()
    
    def close(self):
        """Chiude dialog"""
        try:
            self.progress.stop()
            self.dialog.destroy()
        except:
            pass


class ResultsDialog:
    """Dialog per mostrare risultati"""
    
    def __init__(self, parent, title, content):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Text area
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_area = tk.Text(text_frame, wrap=tk.WORD, font=("Courier", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area.insert(1.0, content)
        text_area.config(state=tk.DISABLED)  # Read-only
        
        # Close button
        ttk.Button(main_frame, text="Chiudi", 
                  command=self.dialog.destroy).pack(pady=(10, 0))


class AutoDateCalculatorDialog:
    """Dialog per calcolo automatico date"""
    
    def __init__(self, parent, cert_id, cert_data):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Calcolo Automatico Date - {cert_id}")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.cert_data = cert_data
        self._setup_form()
    
    def _setup_form(self):
        """Setup form calcolo automatico"""
        
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        ttk.Label(main_frame, text="Calcolo Automatico Date Cedole", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 20))
        
        # Frequency
        freq_frame = ttk.LabelFrame(main_frame, text="Frequenza Cedole")
        freq_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.frequency_var = tk.StringVar(value="Q")
        
        freq_options = [
            ("M", "Mensile"),
            ("Q", "Trimestrale"),
            ("S", "Semestrale"),
            ("A", "Annuale")
        ]
        
        for value, text in freq_options:
            ttk.Radiobutton(freq_frame, text=text, variable=self.frequency_var, 
                           value=value).pack(anchor=tk.W, padx=10, pady=2)
        
        # Annual rate
        rate_frame = ttk.LabelFrame(main_frame, text="Tasso Annuale")
        rate_frame.pack(fill=tk.X, pady=(0, 10))
        
        rate_inner = ttk.Frame(rate_frame)
        rate_inner.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(rate_inner, text="Tasso Annuale (%):").pack(side=tk.LEFT)
        self.rate_entry = ttk.Entry(rate_inner, width=10)
        self.rate_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.rate_entry.insert(0, "8.0")  # Default 8%
        
        # Info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = f"""Date del certificato:
Emissione: {self.cert_data.get('issue_date', 'N/A')}
Scadenza: {self.cert_data.get('maturity_date', 'N/A')}

Il calcolo automatico sostituirà tutte le date
e i tassi esistenti."""
        
        ttk.Label(info_frame, text=info_text, font=("Arial", 9)).pack()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Annulla", 
                  command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Calcola Date", 
                  command=self._calculate).pack(side=tk.RIGHT)
    
    def _calculate(self):
        """Calcola date automaticamente"""
        
        try:
            # Parse parametri
            frequency = self.frequency_var.get()
            annual_rate = float(self.rate_entry.get()) / 100  # Convert percentage
            
            # Parse date
            issue_date = self.cert_data.get('issue_date', '')
            maturity_date = self.cert_data.get('maturity_date', '')
            
            if isinstance(issue_date, str):
                issue_date = datetime.fromisoformat(issue_date)
            if isinstance(maturity_date, str):
                maturity_date = datetime.fromisoformat(maturity_date)
            
            # Calcola date
            coupon_dates = self._calculate_coupon_dates(issue_date, maturity_date, frequency)
            
            # Calcola rates
            frequency_map = {'M': 12, 'Q': 4, 'S': 2, 'A': 1}
            periods_per_year = frequency_map[frequency]
            period_rate = annual_rate / periods_per_year
            
            coupon_rates = [period_rate] * len(coupon_dates)
            autocall_levels = [1.0] * len(coupon_dates)  # Default 100%
            
            # Risultato
            self.result = {
                'coupon_dates': [d.isoformat() for d in coupon_dates],
                'coupon_rates': coupon_rates,
                'autocall_levels': autocall_levels,
                'coupon_frequency': frequency,
                'annual_coupon_rate': annual_rate
            }
            
            messagebox.showinfo("Calcolo Completato", 
                              f"Calcolate {len(coupon_dates)} date cedole\n"
                              f"Frequenza: {frequency}\n"
                              f"Tasso periodo: {period_rate:.3%}")
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore calcolo date:\n{e}")
    
    def _calculate_coupon_dates(self, issue_date, maturity_date, frequency):
        """Calcola date cedole"""
        
        months_map = {'M': 1, 'Q': 3, 'S': 6, 'A': 12}
        months_inc = months_map[frequency]
        
        coupon_dates = []
        current_date = issue_date
        
        # Prima data
        next_month = current_date.month + months_inc
        next_year = current_date.year
        if next_month > 12:
            next_year += (next_month - 1) // 12
            next_month = ((next_month - 1) % 12) + 1
        
        current_date = current_date.replace(year=next_year, month=next_month)
        
        # Genera date
        while current_date < maturity_date:
            coupon_dates.append(current_date)
            
            next_month = current_date.month + months_inc
            next_year = current_date.year
            if next_month > 12:
                next_year += (next_month - 1) // 12
                next_month = ((next_month - 1) % 12) + 1
            
            current_date = current_date.replace(year=next_year, month=next_month)
        
        # Aggiungi maturity
        coupon_dates.append(maturity_date)
        
        return coupon_dates
    
    def _cancel(self):
        """Annulla dialog"""
        self.result = None
        self.dialog.destroy()


# ========================================
# MAIN
# ========================================

def main():
    """Main function"""
    
    print("🖥️  SIMPLE GUI MANAGER")
    print("GUI funzionante per gestione certificati")
    print("="*50)
    
    try:
        gui = SimpleCertificateGUI()
        gui.run()
    except Exception as e:
        print(f"❌ Errore GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    main()
