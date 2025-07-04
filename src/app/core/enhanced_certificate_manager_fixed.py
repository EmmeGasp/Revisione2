# ==========================================================
# RIEPILOGO CONTENUTO FILE:
# - Classi: EnhancedCertificateConfig, InLifeCertificateState, YahooFinanceDataProvider, DateCalculationUtils
# - Classe principale: EnhancedCertificateManagerV15 (gestione certificati avanzata)
# - Classi GUI: CalculoDateAutoDialogV15, PreviewDialog
# - Funzioni di test e integrazione con GUI v14
# ==========================================================

# ========================================
# ENHANCED CERTIFICATE MANAGER - VERSIONE CORRETTA v15
# Tutte le correzioni integrate: yahoo_ticker, calcolo date, dimensioni finestre
# ========================================

"""
*** ENHANCED CERTIFICATE MANAGER - VERSIONE CORRETTA v15 ***

CORREZIONI INTEGRATE:
✅ yahoo_ticker opzionale in tutte le configurazioni
✅ Fix errore "day out of range" nel calcolo date 
✅ Dimensioni finestre calcolo date corrette
✅ Valori default caricati dal certificato selezionato
✅ Gestione robusta errori Yahoo Finance
✅ Validazione completa dati input
✅ Backward compatibility con configurazioni esistenti

COMPATIBILITÀ:
✅ Funziona con fixed_gui_v15_1_corrected.py
✅ Supporta formato enhanced e basic
✅ Auto-migrazione configurazioni esistenti
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pathlib import Path
import yfinance as yf
import threading
import calendar

# Import dal sistema esistente
from app.utils.real_certificate_integration import (
    RealCertificateConfig, IntegratedCertificateSystem,
    RealCertificateImporter
)

# ========================================
# *** VERSIONE CORRETTA *** - ENHANCED CONFIG CON YAHOO_TICKER
# ========================================

class InLifeCertificateState:
    """Stato certificato in-life per valutazione corrente - VERSIONE CORRETTA"""
    
    def __init__(self):
        self.valuation_date = datetime.now()
        self.paid_coupons = []  # Lista date cedole già pagate
        self.memory_coupons_due = []  # Cedole in memoria non pagate
        self.autocall_events_occurred = []  # Eventi autocall già verificati
        self.barrier_breaches = []  # Rotture barriera passate
        self.current_market_data = {}  # Dati mercato aggiornati
        
        # Flags stato
        self.is_active = True
        self.was_autocalled = False
        self.autocall_date = None
        self.final_payoff = None

class EnhancedCertificateConfig:
    """*** VERSIONE CORRETTA *** - Config con supporto yahoo_ticker e in-life"""
    
    def __init__(self, base_config: RealCertificateConfig):
        # Copia configurazione base
        self.base_config = base_config
        
        # *** VERIFICA YAHOO_TICKER *** - Assicura compatibilità
        if not hasattr(self.base_config, 'yahoo_ticker'):
            self.base_config.yahoo_ticker = None
        
        # Stato in-life
        self.in_life_state = InLifeCertificateState()
        
        # Metadati enhanced
        self.metadata = {
            'created_date': datetime.now(),
            'last_updated': datetime.now(),
            'data_source': 'manual',
            'validation_status': 'pending',
            'notes': '',
            'version': 'v15'  # *** VERSIONE CORRETTA ***
        }
        
        # Stato certificato
        self.status = self._determine_status()
    
    def _determine_status(self):
        """Determina lo stato del certificato: new, in_life, matured, autocalled"""
        today = datetime.now().date()
        issue = self.base_config.issue_date.date() if hasattr(self.base_config, 'issue_date') else None
        maturity = self.base_config.maturity_date.date() if hasattr(self.base_config, 'maturity_date') else None
        val_date = self.in_life_state.valuation_date.date() if hasattr(self.in_life_state, 'valuation_date') else None

        if getattr(self.in_life_state, 'was_autocalled', False):
            return "autocalled"
        if maturity and val_date and val_date >= maturity:
            return "matured"
        if issue and val_date and val_date == issue and not self.in_life_state.paid_coupons and not self.in_life_state.memory_coupons_due:
            return "new"
        return "in_life"
    
    def update_in_life_state(self, valuation_date: datetime = None,
                           paid_coupons: List[datetime] = None,
                           memory_coupons: List[datetime] = None):
        """Aggiorna stato in-life del certificato"""
        
        if valuation_date:
            self.in_life_state.valuation_date = valuation_date
        
        if paid_coupons:
            self.in_life_state.paid_coupons = paid_coupons
            
        if memory_coupons:
            self.in_life_state.memory_coupons_due = memory_coupons
        
        # Aggiorna stato
        self.status = self._determine_status()
        
        self.metadata['last_updated'] = datetime.now()
    
    def get_remaining_coupon_dates(self) -> List[datetime]:
        """Ottiene date cedole rimanenti dalla valuation date"""
        
        valuation_date = self.in_life_state.valuation_date
        all_coupon_dates = self.base_config.coupon_dates or []
        
        # Filtra solo date future
        remaining_dates = [
            date for date in all_coupon_dates 
            if date > valuation_date
        ]
        
        return remaining_dates
    
    def get_memory_coupon_amount(self) -> float:
        """Calcola importo cedole memoria accumulate"""
        
        memory_dates = self.in_life_state.memory_coupons_due
        if not memory_dates:
            return 0.0
        
        # Calcola valore cedole perse
        coupon_rates = self.base_config.coupon_rates or []
        notional = self.base_config.notional
        
        memory_amount = 0.0
        for date in memory_dates:
            # Trova rate corrispondente (semplificato)
            if coupon_rates:
                rate = coupon_rates[0]  # Assumiamo rate costante per semplicità
                memory_amount += notional * rate
        
        return memory_amount

# ========================================
# *** VERSIONE CORRETTA *** - YAHOO FINANCE CON SUPPORTO YAHOO_TICKER
# ========================================

class YahooFinanceDataProvider:
    """*** VERSIONE CORRETTA *** - Provider con gestione yahoo_ticker opzionale"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minuti
    
    def get_ticker_mapping(self) -> Dict[str, str]:
        """Mapping asset names → Yahoo tickers - VERSIONE ESTESA"""
        return {
            # Banche italiane
            'BMPS.MI': 'BMPS.MI',
            'BAMI.MI': 'BAMI.MI', 
            'UCG.MI': 'UCG.MI',
            'ISP.MI': 'ISP.MI',
            'BPER.MI': 'BPER.MI',
            'UBI.MI': 'UBI.MI',
            
            # Indici principali
            '^STOXX50E': '^STOXX50E',
            '^GSPC': '^GSPC',
            '^N225': '^N225',
            '^FTMIB': 'FTSEMIB.MI',
            '^FTSE': '^FTSE',
            '^GDAXI': '^GDAXI',
            
            # Utilities/Energy italiane
            'ENEL.MI': 'ENEL.MI',
            'ENI.MI': 'ENI.MI',
            'TIT.MI': 'TIT.MI',
            'TEN.MI': 'TEN.MI',
            
            # Assicurazioni italiane
            'G.MI': 'G.MI',
            'UNI.MI': 'UNI.MI',
            
            # Tech/Telecom
            'TIM.MI': 'TIM.MI',
            'STM.MI': 'STM.MI'
        }
    
    def get_ticker_for_asset(self, asset: str, yahoo_ticker: Optional[str] = None) -> str:
        """*** NUOVO METODO *** - Ottiene ticker Yahoo con fallback intelligente"""
        
        # Priorità 1: yahoo_ticker specificato
        if yahoo_ticker:
            print(f"📊 Usando ticker specificato per {asset}: {yahoo_ticker}")
            return yahoo_ticker
        
        # Priorità 2: Mapping predefinito
        ticker_mapping = self.get_ticker_mapping()
        if asset in ticker_mapping:
            mapped_ticker = ticker_mapping[asset]
            print(f"📊 Ticker mappato per {asset}: {mapped_ticker}")
            return mapped_ticker
        
        # Priorità 3: Usa asset name direttamente
        print(f"📊 Ticker fallback per {asset}: {asset}")
        return asset
    
    def fetch_market_data_safe(self, assets: List[str], 
                              yahoo_tickers: Optional[List[str]] = None,
                              start_date: datetime = None,
                              end_date: datetime = None) -> Dict:
        """*** VERSIONE CORRETTA *** - Fetch con gestione yahoo_ticker e errori"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=252)  # 1 anno
        if not end_date:
            end_date = datetime.now()
        
        market_data = {
            'spots': {},
            'volatilities': {},
            'returns': {},
            'error_assets': [],
            'warnings': []
        }
        
        print(f"📊 Fetch market data per {len(assets)} assets...")
        
        for i, asset in enumerate(assets):
            try:
                # *** GESTIONE YAHOO_TICKER *** - Priorità intelligente
                if yahoo_tickers and i < len(yahoo_tickers) and yahoo_tickers[i]:
                    yahoo_ticker = yahoo_tickers[i]
                elif yahoo_tickers and len(yahoo_tickers) == 1 and len(assets) == 1:
                    yahoo_ticker = yahoo_tickers[0]
                else:
                    yahoo_ticker = None
                
                ticker = self.get_ticker_for_asset(asset, yahoo_ticker)
                
                # Download dati con timeout
                print(f"   🔄 Downloading {asset} ({ticker})...")
                
                ticker_obj = yf.Ticker(ticker)
                hist = ticker_obj.history(start=start_date, end=end_date, timeout=10)
                
                if hist.empty:
                    print(f"   ⚠️  Nessun dato per {asset} ({ticker})")
                    market_data['error_assets'].append(asset)
                    market_data['warnings'].append(f"Nessun dato per {asset}")
                    continue
                
                # Verifica dati sufficienti
                if len(hist) < 10:
                    print(f"   ⚠️  Dati insufficienti per {asset}: {len(hist)} giorni")
                    market_data['warnings'].append(f"Dati limitati per {asset}")
                
                # Calcola metriche
                current_price = float(hist['Close'].iloc[-1])
                returns = hist['Close'].pct_change().dropna()
                
                if len(returns) > 0:
                    volatility = float(returns.std() * np.sqrt(252))  # Annualizzata
                else:
                    volatility = 0.20  # Default fallback
                    market_data['warnings'].append(f"Volatilità default per {asset}")
                
                market_data['spots'][asset] = current_price
                market_data['volatilities'][asset] = volatility
                market_data['returns'][asset] = returns.tolist()
                
                print(f"   ✅ {asset}: €{current_price:.2f}, Vol={volatility:.2%}")
                
            except Exception as e:
                print(f"   ❌ Errore fetch {asset}: {e}")
                market_data['error_assets'].append(asset)
                market_data['warnings'].append(f"Errore {asset}: {str(e)}")
        
        # Summary
        success_count = len(market_data['spots'])
        total_count = len(assets)
        print(f"📊 Fetch completato: {success_count}/{total_count} successi")
        
        return market_data

    # NEW CODE v16.1 - con debug tracciamento dati:
    def update_certificate_market_data(self, config: 'EnhancedCertificateConfig') -> bool:
        """*** VERSIONE CORRETTA V16.1*** - Update con debug tracciamento dati"""
        
        try:
            assets = config.base_config.underlying_assets

            # *** DEBUG v16.1 *** - Stato PRIMA del fetch
            print(f"🔍 DEBUG v16.1 - PRIMA del fetch Yahoo:")
            if hasattr(config.base_config, 'current_spots') and config.base_config.current_spots:
                print(f"   Current spots esistenti: {config.base_config.current_spots}")
            else:
                print(f"   Current spots: Non definiti")
    

            
            # *** GESTIONE YAHOO_TICKER FLESSIBILE ***
            yahoo_ticker = getattr(config.base_config, 'yahoo_ticker', None)
            
            # Converte yahoo_ticker in lista se necessario
            yahoo_tickers = None
            if yahoo_ticker:
                if isinstance(yahoo_ticker, str):
                    # Singolo ticker - potrebbe essere per tutti gli asset o solo il primo
                    if len(assets) == 1:
                        yahoo_tickers = [yahoo_ticker]
                    else:
                        # Assume che sia per il primo asset
                        yahoo_tickers = [yahoo_ticker] + [None] * (len(assets) - 1)
                elif isinstance(yahoo_ticker, list):
                    yahoo_tickers = yahoo_ticker
                else:
                    print(f"⚠️  Formato yahoo_ticker non riconosciuto: {type(yahoo_ticker)}")
            
            # Fetch dati
            market_data = self.fetch_market_data_safe(assets, yahoo_tickers)
            # *** DEBUG v16.1 *** - Stato DOPO il fetch
            print(f"🔍 DEBUG v16.1 - DOPO il fetch Yahoo:")
            print(f"   Dati scaricati spots: {market_data.get('spots', {})}")


            # Aggiorna config con dati disponibili
            if market_data['spots']:
                # Usa dati fetch o fallback
                config.base_config.current_spots = []
                config.base_config.volatilities = []
                
                for asset in assets:
                    if asset in market_data['spots']:
                        config.base_config.current_spots.append(market_data['spots'][asset])
                        config.base_config.volatilities.append(market_data['volatilities'][asset])
                    else:
                        # Fallback defaults
                        config.base_config.current_spots.append(100.0)
                        config.base_config.volatilities.append(0.25)
                        print(f"   ⚠️  Usando default per {asset}")
                
                # Aggiorna metadata
                config.in_life_state.current_market_data = market_data
                config.metadata['data_source'] = 'yahoo'
                config.metadata['last_updated'] = datetime.now()
                
                # Statistiche finali
                errors = len(market_data['error_assets'])
                warnings = len(market_data['warnings'])
                
                # *** DEBUG v16.1 *** - Stato FINALE
                print(f"🔍 DEBUG v16.1 - STATO FINALE:")
                print(f"   Current spots finali: {config.base_config.current_spots}")                
                
                if errors == 0:
                    print(f"✅ Market data aggiornati completamente")
                    return True
                elif errors < len(assets):
                    print(f"⚠️  Market data aggiornati parzialmente ({errors} errori, {warnings} warnings)")
                    return True
                else:
                    print(f"❌ Tutti i fetch falliti")
                    return False
            else:
                print("❌ Nessun dato market recuperato")
                return False
           
    
        except Exception as e:
            print(f"❌ Errore update market data: {e}")
            import traceback
            traceback.print_exc()
            return False

# ========================================
# *** VERSIONE CORRETTA *** - CALCOLO DATE ROBUSTO
# ========================================

class DateCalculationUtils:
    """*** VERSIONE CORRETTA *** - Utility per calcolo date senza errori"""
    
    @staticmethod
    def calculate_coupon_dates_robust(start_date: datetime, end_date: datetime, 
                                    frequency: str) -> List[datetime]:
        """*** VERSIONE ROBUSTA *** - Calcolo date senza errore 'day out of range'"""
        
        print(f"📅 Calcolo date robusto v15:")
        print(f"   Start: {start_date.strftime('%Y-%m-%d')}")
        print(f"   End: {end_date.strftime('%Y-%m-%d')}")
        print(f"   Frequency: {frequency}")
        
        # Mapping frequenze
        interval_months = {
            "Mensile": 1, "M": 1,
            "Bimestrale": 2, "B": 2, # Aggiunto Bimestrale
            "Trimestrale": 3, "Q": 3,
            "Quadrimestrale": 4, "R": 4, # Aggiunto Quadrimestrale
            "Semestrale": 6, "S": 6,
            "Annuale": 12, "A": 12
        }
        
        if frequency not in interval_months:
            raise ValueError(f"Frequenza non supportata: {frequency}")
        
        months_interval = interval_months[frequency]
        coupon_dates = []
        
        # Inizia dal primo periodo
        current_year = start_date.year
        current_month = start_date.month + months_interval
        target_day = start_date.day
        
        # Aggiusta anno se necessario
        while current_month > 12:
            current_month -= 12
            current_year += 1
        
        print(f"   Primo periodo: {current_year}-{current_month:02d}-{target_day:02d}")
        
        # Genera tutte le date
        iteration = 0
        while iteration < 500:  # Safety limit aumentato
            
            # *** FIX CRITICO *** - Gestisce giorni inesistenti nel mese
            try:
                # Verifica se il giorno esiste nel mese
                last_day_of_month = calendar.monthrange(current_year, current_month)[1]
                actual_day = min(target_day, last_day_of_month)
                
                current_date = datetime(current_year, current_month, actual_day)
                
                print(f"   Data generata: {current_date.strftime('%Y-%m-%d')}")
                
                # Verifica se supera la data di fine
                if current_date > end_date:
                    print(f"   Fermato: data supera end_date")
                    break
                
                coupon_dates.append(current_date)
                
            except ValueError as date_error:
                print(f"   ❌ Errore creazione data {current_year}-{current_month:02d}-{actual_day:02d}: {date_error}")
                
                # Fallback: usa ultimo giorno del mese
                try:
                    last_day = calendar.monthrange(current_year, current_month)[1]
                    current_date = datetime(current_year, current_month, last_day)
                    
                    if current_date <= end_date:
                        coupon_dates.append(current_date)
                        print(f"   🔧 Fallback data: {current_date.strftime('%Y-%m-%d')}")
                    else:
                        break
                        
                except Exception as fallback_error:
                    print(f"   ❌ Anche fallback fallito: {fallback_error}")
                    break
            
            # Incrementa al prossimo periodo
            current_month += months_interval
            while current_month > 12:
                current_month -= 12
                current_year += 1
            
            iteration += 1
        
        # *** VERIFICA FINALE *** - Assicura che maturity sia inclusa
        if coupon_dates and coupon_dates[-1] != end_date:
            # Solo se maturity è dopo l'ultima cedola
            if end_date > coupon_dates[-1]:
                coupon_dates.append(end_date)
                print(f"   📌 Maturity aggiunta: {end_date.strftime('%Y-%m-%d')}")
        elif not coupon_dates:
            # Caso estremo: almeno maturity
            coupon_dates.append(end_date)
            print(f"   🚨 Solo maturity: {end_date.strftime('%Y-%m-%d')}")
        
        print(f"📊 Totale {len(coupon_dates)} date cedole generate (robusto v15)")
        
        # Verifica ordine cronologico
        for i in range(1, len(coupon_dates)):
            if coupon_dates[i] <= coupon_dates[i-1]:
                print(f"   ⚠️  Warning: date non in ordine cronologico")
                break
        
        return coupon_dates
    
    @staticmethod
    def validate_coupon_schedule(coupon_dates: List[datetime], 
                               coupon_rates: List[float]) -> Tuple[bool, str]:
        """Valida coerenza schedule cedole"""
        
        if not coupon_dates:
            return False, "Nessuna data cedola specificata"
        
        if not coupon_rates:
            return False, "Nessun tasso cedola specificato"
        
        if len(coupon_dates) != len(coupon_rates):
            return False, f"Mismatch: {len(coupon_dates)} date vs {len(coupon_rates)} tassi"
        
        # Verifica ordine cronologico
        for i in range(1, len(coupon_dates)):
            if coupon_dates[i] <= coupon_dates[i-1]:
                return False, f"Date non in ordine cronologico: {coupon_dates[i-1]} >= {coupon_dates[i]}"
        
        # Verifica tassi validi
        for i, rate in enumerate(coupon_rates):
            if not (0 <= rate <= 1):
                return False, f"Tasso {i+1} fuori range [0,1]: {rate}"
        
        return True, "Schedule valida"

# ========================================
# *** VERSIONE CORRETTA *** - ENHANCED CERTIFICATE MANAGER
# ========================================

class EnhancedCertificateManagerV15:
    """*** VERSIONE CORRETTA v15 *** - Manager completo con tutte le correzioni"""
    
    def __init__(self, config_dir="D:/Doc/File python/Finanza/Certificates/Revisione2/src/app/data"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Storage
        self.configurations = {}  # Dict[str, EnhancedCertificateConfig]
        self.portfolio_configs = {}
        
        # Files
        self.config_file = self.config_dir / "certificates.json"
        self.portfolio_file = self.config_dir / "portfolios.json"
        
        # Fallback ai file precedenti
        if not self.config_file.exists():
            old_file = self.config_dir / "enhanced_certificates.json"
            if old_file.exists():
                print(f"🔄 Migrazione da {old_file} a {self.config_file}")
                import shutil
                shutil.copy2(old_file, self.config_file)
        
        # Providers - *** VERSIONE CORRETTA ***
        self.yahoo_provider = YahooFinanceDataProvider()
        self.integrated_system = IntegratedCertificateSystem()
        self.date_utils = DateCalculationUtils()
        
        # Load existing
        self._load_configurations()
        
        print(f"🚀 Enhanced Certificate Manager v15 inizializzato")
        print(f"   Directory: {self.config_dir}")
        print(f"   Certificati: {len(self.configurations)}")
        print(f"   Portfolio: {len(self.portfolio_configs)}")
        print(f"   Versione: v15 (CORRETTA)")
    
    def add_certificate_from_dict_v15(self, cert_id: str, config_dict: Dict,
                                     valuation_date: datetime = None) -> EnhancedCertificateConfig:
        """*** VERSIONE CORRETTA v15 *** - Aggiunge certificato con validazione completa"""
        
        try:
            print(f"🆕 Aggiunta certificato v15: {cert_id}")
            print(f"   Dati ricevuti: {list(config_dict.keys())}")
            
            # Debug yahoo_ticker
            yahoo_ticker = config_dict.get('yahoo_ticker')
            if yahoo_ticker:
                print(f"   📊 Yahoo ticker specificato: {yahoo_ticker}")
            
            # *** CONVERSIONE SICURA *** - Con supporto yahoo_ticker
            base_config = self._dict_to_real_config_safe_v15(config_dict)
            
            # Valida schedule cedole se presente
            if base_config.coupon_dates and base_config.coupon_rates:
                is_valid, message = self.date_utils.validate_coupon_schedule(
                    base_config.coupon_dates, base_config.coupon_rates
                )
                if not is_valid:
                    print(f"⚠️  Warning schedule cedole: {message}")
            
            # Crea enhanced config
            enhanced_config = EnhancedCertificateConfig(base_config)
            
            # Setup in-life state
            if valuation_date:
                enhanced_config.in_life_state.valuation_date = valuation_date
            
            # Auto-update market data con supporto yahoo_ticker
            if config_dict.get('auto_update_market_data', True):
                print(f"📊 Auto-updating market data per {cert_id}...")
                success = self.yahoo_provider.update_certificate_market_data(enhanced_config)
                if success:
                    print(f"✅ Market data aggiornati da Yahoo Finance")
                else:
                    print(f"⚠️  Alcuni dati market falliti, usando defaults")
            
            # Salva
            self.configurations[cert_id] = enhanced_config
            self._save_configurations()
            
            print(f"✅ Certificato enhanced {cert_id} aggiunto (v15)")
            return enhanced_config
            
        except Exception as e:
            print(f"❌ Errore aggiunta certificato {cert_id}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _dict_to_real_config_safe_v15(self, config_dict: Dict) -> RealCertificateConfig:
        
        """
        *** VERSIONE CORRETTA v15.1 *** - SOSTITUISCI IL METODO ESISTENTE
    
        TROVA nel file enhanced_certificate_manager_fixed.py:
        def _dict_to_real_config_safe_v15(self, config_dict: Dict) -> RealCertificateConfig:
            
        E SOSTITUISCI tutto il contenuto con questo codice:
        """
      
        print(f"🔄 === CONVERSIONE SAFE v15.1 (Enhanced Manager) ===")
        print(f"📊 Input keys: {list(config_dict.keys())}")
        
        # *** STEP 1: GESTIONE YAHOO_TICKER GARANTITA ***
        if 'yahoo_ticker' not in config_dict:
            config_dict['yahoo_ticker'] = None
            print(f"   📊 yahoo_ticker non specificato, impostato a None")
        
        # *** STEP 2: CONVERSIONE CAMPI v15.1 -> RealCertificateConfig ***
        
        # Lista campi supportati da RealCertificateConfig
        supported_fields = {
            'isin', 'name', 'certificate_type', 'issuer', 'underlying_assets',
            'issue_date', 'maturity_date', 'notional', 'currency', 'yahoo_ticker',
            'coupon_rates', 'coupon_dates', 'autocall_levels', 'autocall_dates',
            'barrier_levels', 'memory_feature', 'current_spots', 'volatilities',
            'correlations', 'risk_free_rate', 'dividend_yields',
            'certificate_instrument_ticker', 'underlying_currencies', 'underlying_names', 'underlying_dependency_type', # Nuovi campi
            'dynamic_barrier_feature', 'dynamic_barrier_start_level', 'step_down_rate', 'dynamic_barrier_end_level' # Nuovi campi barriera dinamica
        }
        
        # Filtra campi supportati
        filtered_config = {}
        excluded_fields = []
        
        for key, value in config_dict.items():
            if key in supported_fields:
                filtered_config[key] = value
            else:
                excluded_fields.append(key)
        
        print(f"🔧 Campi esclusi v15.1: {excluded_fields}")
        
        # *** STEP 3: CONVERSIONE BARRIERE v15.1 ***
        barrier_levels = {}
        
        # Converte barriera cedola v15.1 -> barrier_levels['coupon']
        if 'coupon_barrier_value' in config_dict:
            coupon_value = config_dict['coupon_barrier_value']
            if isinstance(coupon_value, (int, float)) and coupon_value > 0:
                barrier_levels['coupon'] = coupon_value
                print(f"🔄 Barriera cedola convertita: {coupon_value}")
        
        # Converte barriera capitale v15.1 -> barrier_levels['capital']  
        if 'capital_barrier_value' in config_dict:
            capital_value = config_dict['capital_barrier_value']
            if isinstance(capital_value, (int, float)) and capital_value > 0:
                barrier_levels['capital'] = capital_value
                print(f"🔄 Barriera capitale convertita: {capital_value}")
        
        # Converte airbag v15.1 -> barrier_levels['airbag']
        if config_dict.get('airbag_feature') and 'airbag_level' in config_dict:
            airbag_value = config_dict['airbag_level']
            if isinstance(airbag_value, (int, float)) and airbag_value > 0:
                barrier_levels['airbag'] = airbag_value
                print(f"🔄 Airbag convertito: {airbag_value}")
        
        # Aggiungi barrier_levels convertite
        if barrier_levels:
            filtered_config['barrier_levels'] = barrier_levels
            print(f"✅ barrier_levels creato: {barrier_levels}")
        
        # *** STEP 4: GESTIONE DATE SICURA ***
        
        # Gestione date singole
        for date_field in ['issue_date', 'maturity_date']:
            if isinstance(filtered_config.get(date_field), str):
                try:
                    filtered_config[date_field] = datetime.fromisoformat(filtered_config[date_field])
                except ValueError as e:
                    print(f"⚠️ Errore parsing {date_field}: {e}")
                    # Fallback a data default
                    if date_field == 'issue_date':
                        filtered_config[date_field] = datetime.now()
                    else:
                        filtered_config[date_field] = datetime.now() + timedelta(days=365*5)
        
        # Gestione date lists
        for date_list_field in ['coupon_dates', 'autocall_dates']:
            if filtered_config.get(date_list_field):
                parsed_dates = []
                for date_item in filtered_config[date_list_field]:
                    if isinstance(date_item, str):
                        try:
                            parsed_dates.append(datetime.fromisoformat(date_item))
                        except ValueError as e:
                            print(f"⚠️ Errore parsing date in {date_list_field}: {e}")
                    elif isinstance(date_item, datetime):
                        parsed_dates.append(date_item)
                
                filtered_config[date_list_field] = parsed_dates
        
        # *** STEP 5: GESTIONE CORRELATIONS ***
        if filtered_config.get('correlations'):
            if isinstance(filtered_config['correlations'], list):
                try:
                    import numpy as np
                    filtered_config['correlations'] = np.array(filtered_config['correlations'])
                except Exception as e:
                    print(f"⚠️ Errore conversione correlations: {e}")
                    # Rimuovi per usare default
                    del filtered_config['correlations']
        
        # *** STEP 6: GESTIONE UNDERLYING ASSETS ***
        if 'underlying_assets' in filtered_config:
            if isinstance(filtered_config['underlying_assets'], str):
                # Singolo asset
                filtered_config['underlying_assets'] = [filtered_config['underlying_assets']]
        
        # *** STEP 7: CREAZIONE RealCertificateConfig ***
        try:
            from app.utils.real_certificate_integration import RealCertificateConfig
            real_config = RealCertificateConfig(**filtered_config)
            
            print(f"✅ RealCertificateConfig creato (Enhanced Manager v15.1)")
            print(f"📊 Campi utilizzati: {len(filtered_config)}")
            
            return real_config
            
        except Exception as e:
            print(f"❌ ERRORE CRITICO creazione RealCertificateConfig: {e}")
            print(f"📊 Filtered config keys: {list(filtered_config.keys())}")
            
            # Debug dettagliato
            for key, value in filtered_config.items():
                print(f"   {key}: {type(value)} = {value}")
            
            raise Exception(f"Impossibile creare RealCertificateConfig: {e}")


    def calculate_coupon_dates_for_certificate(self, cert_id: str, 
                                             frequency: str, 
                                             period_rate: float) -> Dict:
        """*** NUOVO METODO v15 *** - Calcola date cedole per certificato esistente"""
        
        if cert_id not in self.configurations:
            raise ValueError(f"Certificato {cert_id} non trovato")
        
        enhanced_config = self.configurations[cert_id]
        base_config = enhanced_config.base_config
        
        print(f"📅 Calcolo date cedole v15 per {cert_id}")
        print(f"   Frequency: {frequency}")
        print(f"   Period rate: {period_rate:.4f}")
        
        try:
            # Usa il calcolo robusto
            coupon_dates = self.date_utils.calculate_coupon_dates_robust(
                base_config.issue_date,
                base_config.maturity_date,
                frequency
            )
            
            # Crea rates array
            coupon_rates = [period_rate] * len(coupon_dates)
            autocall_levels = [1.0] * len(coupon_dates)  # Default 100%
            
            # Calcola tasso annuo equivalente
            frequency_map = {'M': 12, 'Mensile': 12, 'Q': 4, 'Trimestrale': 4, 
                           'S': 2, 'Semestrale': 2, 'A': 1, 'Annuale': 1,
                           'Bimestrale': 6, 'Quadrimestrale': 3} # Aggiunti
            periods_per_year = frequency_map.get(frequency, 4)
            annual_equivalent = period_rate * periods_per_year
            
            # Aggiorna configurazione
            base_config.coupon_dates = coupon_dates
            base_config.coupon_rates = coupon_rates
            base_config.autocall_levels = autocall_levels
            
            # Metadata
            enhanced_config.metadata['last_updated'] = datetime.now()
            enhanced_config.metadata['notes'] = f"Date calcolate v15: {frequency} {period_rate:.2%}"
            
            # Salva
            self._save_configurations()
            
            result = {
                'coupon_dates': coupon_dates,
                'coupon_rates': coupon_rates,
                'autocall_levels': autocall_levels,
                'frequency': frequency,
                'period_rate': period_rate,
                'annual_equivalent': annual_equivalent,
                'calculation_method': 'robust_v15'
            }
            
            print(f"✅ Calcolate {len(coupon_dates)} date cedole")
            print(f"   Tasso periodo: {period_rate:.2%}")
            print(f"   Tasso annuo equivalente: {annual_equivalent:.2%}")
            
            return result
            
        except Exception as e:
            print(f"❌ Errore calcolo date cedole: {e}")
            raise
    
    def update_certificate_in_life_state_v15(self, cert_id: str,
                                           valuation_date: datetime = None,
                                           paid_coupons: List[str] = None,
                                           memory_coupons: List[str] = None):
        """*** VERSIONE CORRETTA v15 *** - Aggiorna stato in-life"""
        
        if cert_id not in self.configurations:
            raise ValueError(f"Certificato {cert_id} non trovato")
        
        config = self.configurations[cert_id]
        
        # Converti date strings
        paid_coupon_dates = []
        if paid_coupons:
            for date_str in paid_coupons:
                try:
                    paid_coupon_dates.append(datetime.fromisoformat(date_str))
                except ValueError as e:
                    print(f"⚠️  Errore parsing paid coupon date '{date_str}': {e}")
        
        memory_coupon_dates = []
        if memory_coupons:
            for date_str in memory_coupons:
                try:
                    memory_coupon_dates.append(datetime.fromisoformat(date_str))
                except ValueError as e:
                    print(f"⚠️  Errore parsing memory coupon date '{date_str}': {e}")
        
        # Aggiorna stato
        config.update_in_life_state(
            valuation_date=valuation_date,
            paid_coupons=paid_coupon_dates,
            memory_coupons=memory_coupon_dates
        )
        
        # Salva
        self._save_configurations()
        
        print(f"✅ Stato in-life aggiornato per {cert_id} (v15)")
        print(f"   Valuation Date: {config.in_life_state.valuation_date.strftime('%Y-%m-%d')}")
        print(f"   Paid Coupons: {len(config.in_life_state.paid_coupons)}")
        print(f"   Memory Coupons: {len(config.in_life_state.memory_coupons_due)}")
    
    def process_certificate_in_life_v15(self, cert_id: str, 
                                      create_excel: bool = True) -> Tuple:
        """*** VERSIONE CORRETTA v15 *** - Processa certificato con tutte le correzioni"""
        
        if cert_id not in self.configurations:
            raise ValueError(f"Certificato {cert_id} non trovato")
        
        enhanced_config = self.configurations[cert_id]
        base_config = enhanced_config.base_config
        
        print(f"🔄 Processamento in-life v15: {cert_id}")
        print(f"   Valuation Date: {enhanced_config.in_life_state.valuation_date.strftime('%Y-%m-%d')}")
        print(f"   Yahoo Ticker: {getattr(base_config, 'yahoo_ticker', 'None')}")
        
        # Aggiusta config per in-life valuation
        adjusted_config = self._adjust_config_for_in_life_v15(enhanced_config)
        
        # Processa con sistema integrato
        try:
            certificate, results = self.integrated_system.process_real_certificate(
                adjusted_config, create_excel_report=create_excel
            )
            
            # Aggiusta risultati per memoria
            adjusted_results = self._adjust_results_for_memory_v15(enhanced_config, results)
            
            print(f"✅ Processamento in-life v15 {cert_id} completato")
            
            return certificate, adjusted_results
            
        except Exception as e:
            print(f"❌ Errore processamento {cert_id}: {e}")
            raise
    
    def _adjust_config_for_in_life_v15(self, enhanced_config: EnhancedCertificateConfig) -> RealCertificateConfig:
        """*** VERSIONE CORRETTA v15 *** - Aggiusta config per valutazione in-life"""
        
        base_config = enhanced_config.base_config
        in_life_state = enhanced_config.in_life_state
        
        # Crea nuova config aggiustata con tutti i campi
        adjusted_dict = {
            'isin': base_config.isin,
            'name': f"{base_config.name} (In-Life v15)",
            'certificate_type': base_config.certificate_type,
            'issuer': base_config.issuer,
            'underlying_assets': base_config.underlying_assets,
            'issue_date': in_life_state.valuation_date,  # *** KEY CHANGE ***
            'maturity_date': base_config.maturity_date,
            'notional': base_config.notional,
            'currency': base_config.currency,
            
            # *** NUOVO *** - Mantieni yahoo_ticker
            'yahoo_ticker': getattr(base_config, 'yahoo_ticker', None),
            'certificate_instrument_ticker': getattr(base_config, 'certificate_instrument_ticker', None), # Nuovo
            'underlying_currencies': getattr(base_config, 'underlying_currencies', None), # Nuovo
            'underlying_names': getattr(base_config, 'underlying_names', None), # Nuovo
            'underlying_dependency_type': getattr(base_config, 'underlying_dependency_type', None), # Nuovo
            'dynamic_barrier_feature': getattr(base_config, 'dynamic_barrier_feature', None), # Nuovo
            'dynamic_barrier_start_level': getattr(base_config, 'dynamic_barrier_start_level', None), # Nuovo
            'step_down_rate': getattr(base_config, 'step_down_rate', None), # Nuovo
            'dynamic_barrier_end_level': getattr(base_config, 'dynamic_barrier_end_level', None), # Nuovo

            # Adjusted dates - Solo date future
            'coupon_dates': enhanced_config.get_remaining_coupon_dates(),
            'coupon_rates': base_config.coupon_rates,
            
            # Market data (possibilmente aggiornati)
            'current_spots': base_config.current_spots,
            'volatilities': base_config.volatilities,
            'correlations': base_config.correlations,
            'risk_free_rate': base_config.risk_free_rate,
            'dividend_yields': base_config.dividend_yields,
            
            # Altri parametri
            'autocall_levels': base_config.autocall_levels,
            'barrier_levels': base_config.barrier_levels,
            'memory_feature': base_config.memory_feature
        }
        
        # Aggiusta lunghezza coupon_rates se necessario
        remaining_dates = adjusted_dict['coupon_dates']
        if remaining_dates and base_config.coupon_rates:
            # Usa i rate rimanenti
            original_dates = base_config.coupon_dates or []
            if len(original_dates) == len(base_config.coupon_rates):
                # Trova indice di partenza
                start_index = 0
                for i, orig_date in enumerate(original_dates):
                    if orig_date > in_life_state.valuation_date:
                        start_index = i
                        break
                
                adjusted_dict['coupon_rates'] = base_config.coupon_rates[start_index:start_index + len(remaining_dates)]
            else:
                # Usa primo rate per tutte le date rimanenti
                adjusted_dict['coupon_rates'] = [base_config.coupon_rates[0]] * len(remaining_dates)
        
        return RealCertificateConfig(**adjusted_dict)
    
    def _adjust_results_for_memory_v15(self, enhanced_config: EnhancedCertificateConfig, 
                                     results: Dict) -> Dict:
        """*** VERSIONE CORRETTA v15 *** - Aggiusta risultati per cedole memoria"""
        
        if not results:
            return results
        
        # Calcola valore cedole memoria
        memory_value = enhanced_config.get_memory_coupon_amount()
        
        if memory_value > 0:
            # Aggiusta fair value
            fair_value = results.get('fair_value', {})
            current_fv = fair_value.get('fair_value', 0)
            
            fair_value['fair_value'] = current_fv + memory_value
            fair_value['memory_coupon_value'] = memory_value
            fair_value['base_fair_value'] = current_fv
            fair_value['adjustment_note'] = 'Cedole memoria aggiunte (v15)'
            
            results['fair_value'] = fair_value
            
            print(f"   💰 Cedole memoria aggiunte v15: €{memory_value:.2f}")
        
        return results
    
    # ========================================
    # DATA MANAGEMENT v15
    # ========================================
    
    def _save_configurations(self):
        """*** VERSIONE CORRETTA v15 *** - Salva enhanced configurations"""
        try:
            configs_dict = {}
            for cert_id, enhanced_config in self.configurations.items():
                # Serializza enhanced config
                config_dict = self._enhanced_config_to_dict_v15(enhanced_config)
                configs_dict[cert_id] = config_dict
            
            # Backup automatico
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                import shutil
                shutil.copy2(self.config_file, backup_file)
                print(f"🔄 Backup creato: {backup_file.name}")
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(configs_dict, f, indent=2, default=str, ensure_ascii=False)
                
            print(f"💾 Configurazioni v15 salvate: {len(configs_dict)} certificati")
                
        except Exception as e:
            print(f"❌ Errore salvataggio enhanced configs v15: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_configurations(self):
        """*** VERSIONE CORRETTA v15 *** - Carica enhanced configurations"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    configs_dict = json.load(f)
                
                print(f"📂 Caricamento configurazioni v15: {len(configs_dict)} certificati")
                
                for cert_id, config_dict in configs_dict.items():
                    try:
                        enhanced_config = self._dict_to_enhanced_config_v15(config_dict)
                        self.configurations[cert_id] = enhanced_config
                        print(f"   ✅ {cert_id} caricato")
                    except Exception as e:
                        print(f"   ❌ Errore caricamento {cert_id}: {e}")
            
            # Load portfolios
            if self.portfolio_file.exists():
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    self.portfolio_configs = json.load(f)
                    print(f"📊 Portfolio caricati: {len(self.portfolio_configs)}")
                    
        except Exception as e:
            print(f"❌ Errore caricamento configurazioni v15: {e}")
    
    def _enhanced_config_to_dict_v15(self, enhanced_config: EnhancedCertificateConfig) -> Dict:
        """*** VERSIONE CORRETTA v15 *** - Serializza enhanced config"""
        
        # Base config
        base_dict = self._real_config_to_dict_v15(enhanced_config.base_config)
        
        # In-life state
        in_life_dict = {
            'valuation_date': enhanced_config.in_life_state.valuation_date.isoformat(),
            'paid_coupons': [d.isoformat() for d in enhanced_config.in_life_state.paid_coupons],
            'memory_coupons_due': [d.isoformat() for d in enhanced_config.in_life_state.memory_coupons_due],
            'is_active': enhanced_config.in_life_state.is_active,
            'was_autocalled': enhanced_config.in_life_state.was_autocalled
        }
        
        # Metadata
        metadata_dict = enhanced_config.metadata.copy()
        for key, value in metadata_dict.items():
            if isinstance(value, datetime):
                metadata_dict[key] = value.isoformat()
        
        return {
            'base_config': base_dict,
            'in_life_state': in_life_dict,
            'metadata': metadata_dict,
            'status': getattr(enhanced_config, 'status', 'unknown'),
            'enhanced_version': 'v15'  # *** VERSIONE CORRETTA ***
        }
    
    def _dict_to_enhanced_config_v15(self, config_dict: Dict) -> EnhancedCertificateConfig:
        """*** VERSIONE CORRETTA v15 *** - Deserializza enhanced config"""
        
        # Backward compatibility
        enhanced_version = config_dict.get('enhanced_version', 'unknown')
        
        if enhanced_version == 'unknown' or 'base_config' not in config_dict:
            # Old format - converti direttamente
            print(f"   🔄 Conversione da formato legacy")
            base_config = self._dict_to_real_config_safe_v15(config_dict)
            enhanced_config = EnhancedCertificateConfig(base_config)
            # Mantieni come legacy in metadata
            enhanced_config.metadata['migrated_from'] = 'legacy'
            enhanced_config.metadata['version'] = 'v15'
            return enhanced_config
        
        # New format
        base_dict = config_dict['base_config']
        base_config = self._dict_to_real_config_safe_v15(base_dict)
        
        enhanced_config = EnhancedCertificateConfig(base_config)
        
        # In-life state
        in_life_dict = config_dict.get('in_life_state', {})
        if 'valuation_date' in in_life_dict:
            enhanced_config.in_life_state.valuation_date = datetime.fromisoformat(
                in_life_dict['valuation_date']
            )
        
        if 'paid_coupons' in in_life_dict:
            enhanced_config.in_life_state.paid_coupons = [
                datetime.fromisoformat(d) for d in in_life_dict['paid_coupons']
            ]
        
        if 'memory_coupons_due' in in_life_dict:
            enhanced_config.in_life_state.memory_coupons_due = [
                datetime.fromisoformat(d) for d in in_life_dict['memory_coupons_due']
            ]
        
        # Metadata
        metadata_dict = config_dict.get('metadata', {})
        for key, value in metadata_dict.items():
            if key in ['created_date', 'last_updated'] and isinstance(value, str):
                try:
                    enhanced_config.metadata[key] = datetime.fromisoformat(value)
                except ValueError:
                    enhanced_config.metadata[key] = datetime.now()
            else:
                enhanced_config.metadata[key] = value
        
        # Assicura versione v15
        enhanced_config.metadata['version'] = 'v15'
        
        return enhanced_config
    
    def _real_config_to_dict_v15(self, config: RealCertificateConfig) -> Dict:
        """*** VERSIONE CORRETTA v15 *** - Converte RealCertificateConfig in dict"""
        config_dict = {}
        
        # Copia tutti gli attributi
        for key, value in config.__dict__.items():
            if isinstance(value, datetime):
                config_dict[key] = value.isoformat()
            elif isinstance(value, list) and value and isinstance(value[0], datetime):
                config_dict[key] = [date.isoformat() for date in value]
            elif isinstance(value, np.ndarray):
                config_dict[key] = value.tolist()
            else:
                config_dict[key] = value
        
        return config_dict
    
    def _save_portfolios(self):
        """Salva portfolio configs v15"""
        try:
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio_configs, f, indent=2, default=str, ensure_ascii=False)
            print(f"💾 Portfolio v15 salvati: {len(self.portfolio_configs)}")
        except Exception as e:
            print(f"❌ Errore salvataggio portfolio v15: {e}")
    
    # ========================================
    # UTILITY METHODS v15
    # ========================================
    
    def list_certificates_detailed_v15(self) -> pd.DataFrame:
        """*** VERSIONE CORRETTA v15 *** - Lista certificati con dettagli enhanced"""
        
        data = []
        for cert_id, enhanced_config in self.configurations.items():
            base_config = enhanced_config.base_config
            in_life = enhanced_config.in_life_state
            metadata = enhanced_config.metadata
            
            row = {
                'ISIN': cert_id,
                'Name': base_config.name,
                'Type': base_config.certificate_type,
                'Issuer': base_config.issuer,
                'Yahoo Ticker': getattr(base_config, 'yahoo_ticker', 'N/A'),
                'Issue Date': base_config.issue_date.strftime('%Y-%m-%d'),
                'Maturity Date': base_config.maturity_date.strftime('%Y-%m-%d'),
                'Valuation Date': in_life.valuation_date.strftime('%Y-%m-%d'),
                'Paid Coupons': len(in_life.paid_coupons),
                'Memory Coupons': len(in_life.memory_coupons_due),
                'Is Active': in_life.is_active,
                'Data Source': metadata.get('data_source', 'manual'),
                'Version': metadata.get('version', 'legacy'),
                'Last Updated': metadata.get('last_updated', datetime.now()).strftime('%Y-%m-%d %H:%M') if metadata.get('last_updated') else 'Never'
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def refresh_all_market_data_v15(self):
        """*** VERSIONE CORRETTA v15 *** - Aggiorna dati mercato per tutti i certificati"""
        
        print("🔄 Aggiornamento dati mercato v15 per tutti i certificati...")
        
        updated = 0
        failed = 0
        warnings = 0
        
        for cert_id, enhanced_config in self.configurations.items():
            try:
                print(f"   📊 Aggiornamento {cert_id}...")
                
                success = self.yahoo_provider.update_certificate_market_data(enhanced_config)
                
                if success:
                    updated += 1
                    print(f"   ✅ {cert_id} aggiornato completamente")
                else:
                    warnings += 1
                    print(f"   ⚠️  {cert_id} aggiornato parzialmente")
                    
            except Exception as e:
                failed += 1
                print(f"   ❌ {cert_id} fallito: {e}")
        
        # Salva tutte le modifiche
        self._save_configurations()
        
        print(f"📊 Aggiornamento v15 completato:")
        print(f"   ✅ Successi: {updated}")
        print(f"   ⚠️  Warnings: {warnings}")
        print(f"   ❌ Falliti: {failed}")
        
        return updated, warnings, failed

# ========================================
# *** VERSIONE CORRETTA *** - GUI INTEGRATION
# ========================================

class CalculoDateAutoDialogV15:
    """*** VERSIONE CORRETTA v15 *** - Dialog calcolo date con tutte le correzioni"""
    
    def __init__(self, parent, selected_certificate_id=None, configurations=None):
        self.result = None
        self.selected_certificate_id = selected_certificate_id
        self.configurations = configurations or {}
        
        # *** FIX DIMENSIONI *** - Finestra più grande e ridimensionabile
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Calcolo Automatico Date Cedole v15")
        self.dialog.geometry("700x600")  # *** DIMENSIONI MAGGIORI ***
        self.dialog.resizable(True, True)  # *** RIDIMENSIONABILE ***
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centra finestra
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"700x600+{x}+{y}")
        
        # *** CARICA VALORI DAL CERTIFICATO SELEZIONATO ***
        self._load_certificate_defaults()
        
        # Setup form
        self._setup_form_v15()
        
        print(f"🖥️  Dialog calcolo date v15 aperto per {selected_certificate_id}")
    
    def _load_certificate_defaults(self):
        """*** NUOVO v15 *** - Carica valori default dal certificato selezionato"""
        
        self.default_frequency = "Trimestrale"
        self.default_rate = 2.5
        self.cert_info = "Nessun certificato selezionato"
        
        if (self.selected_certificate_id and 
            self.selected_certificate_id in self.configurations):
            
            cert_data = self.configurations[self.selected_certificate_id]
            print(f"📊 Caricamento defaults da {self.selected_certificate_id}")

            # --- FIX: Prioritize coupon_frequency from cert_data ---
            self.default_frequency = cert_data.get('coupon_frequency', self.default_frequency)
            
            # Determina frequenza dalle date cedole esistenti
            if 'coupon_dates' in cert_data and cert_data['coupon_dates']:
                coupon_dates = cert_data['coupon_dates']
                if len(coupon_dates) >= 2:
                    # Calcola intervallo medio
                    date1_str = coupon_dates[0]
                    date2_str = coupon_dates[1]
                    
                    try:
                        if isinstance(date1_str, str):
                            date1 = datetime.fromisoformat(date1_str)
                        else:
                            date1 = date1_str
                            
                        if isinstance(date2_str, str):
                            date2 = datetime.fromisoformat(date2_str)
                        else:
                            date2 = date2_str
                        
                        delta_days = (date2 - date1).days
                        print(f"   📅 Delta tra cedole: {delta_days} giorni")
                        
                        # Mappa a frequenza
                        if 25 <= delta_days <= 35:
                            self.default_frequency = "Mensile"
                        elif 55 <= delta_days <= 65: # Bimestrale
                            self.default_frequency = "Bimestrale"
                        elif 85 <= delta_days <= 95:
                            self.default_frequency = "Trimestrale"
                        elif 115 <= delta_days <= 125: # Quadrimestrale
                            self.default_frequency = "Quadrimestrale"
                        elif 170 <= delta_days <= 190:
                            self.default_frequency = "Semestrale"
                        elif 350 <= delta_days <= 380:
                            self.default_frequency = "Annuale"
                        
                    except Exception as e:
                        print(f"   ⚠️  Errore calcolo frequenza: {e}")
            
            # Usa il primo coupon rate se disponibile
            if 'coupon_rate' in cert_data: # Usiamo coupon_rate direttamente
                coupon_rate_value = cert_data['coupon_rate']
                if isinstance(coupon_rate_value, (int, float)):
                    # Converti in percentuale per display (se è in decimale)
                    if coupon_rate_value <= 1.0 and coupon_rate_value != 0:
                        self.default_rate = coupon_rate_value * 100
                        # Assicurati che sia almeno 3 decimali per 0.667%
                        if self.default_rate < 1.0: # Se è un piccolo valore percentuale
                            self.default_rate = round(self.default_rate, 3)
                        else:
                            self.default_rate = round(self.default_rate, 2) # Altrimenti 2 decimali
                    else:
                        self.default_rate = round(coupon_rate_value, 2) # Già in percentuale, 2 decimali
                        
                    print(f"   💰 Tasso default dal certificato: {self.default_rate:.2f}%")
            
            # Info certificato
            issue_date = cert_data.get('issue_date', 'N/A')
            maturity_date = cert_data.get('maturity_date', 'N/A')
            name = cert_data.get('name', 'N/A')
            
            self.cert_info = f"""Certificato: {name}
Emissione: {issue_date}
Scadenza: {maturity_date}
Tasso Cedola: {self.default_rate:.3f}% (Frequenza: {self.default_frequency})"""
            
            print(f"   ✅ Defaults caricati: {self.default_frequency}, {self.default_rate}%")
    
    def _setup_form_v15(self):
        """*** VERSIONE CORRETTA v15 *** - Setup form con tutte le correzioni"""
        
        # --- NEW: Main container for scrollable area and fixed bottom frame ---
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollable area
        canvas = tk.Canvas(main_container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        # Frame inside canvas to hold all scrollable content
        scrollable_content_frame = ttk.Frame(canvas)
        
        # Configure scroll region when content changes size
        scrollable_content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_content_frame, anchor="nw")
        
        # Bind canvas to resize its internal window
        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Mouse wheel scroll
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)

        # Fixed bottom frame for buttons
        fixed_bottom_frame = ttk.Frame(main_container)
        fixed_bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Separator above buttons
        ttk.Separator(fixed_bottom_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
        
        # Button frame inside fixed bottom frame
        button_frame = ttk.Frame(fixed_bottom_frame)
        button_frame.pack(fill=tk.X)
        
        # --- END NEW LAYOUT ---

        # *** TITOLO PROMINENTE ***
        title_label = ttk.Label(scrollable_content_frame, 
                               text="Calcolo Automatico Date Cedole v15", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # *** INFORMAZIONI CERTIFICATO ***
        info_frame = ttk.LabelFrame(scrollable_content_frame, text="Certificato Selezionato", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = tk.Text(info_frame, height=5, width=60, wrap=tk.WORD, # Altezza aumentata
                           font=("Arial", 10), state=tk.DISABLED, bg="#f0f0f0")
        info_text.pack(fill=tk.X)
        
        # Popola info
        info_text.config(state=tk.NORMAL)
        info_text.insert(1.0, self.cert_info)
        info_text.config(state=tk.DISABLED)
        
        # *** FREQUENZA CEDOLE ***
        freq_frame = ttk.LabelFrame(scrollable_content_frame, text="Frequenza Cedole", padding="15")
        freq_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.frequency_var = tk.StringVar(value=self.default_frequency)  # *** VALORE DAL CERTIFICATO ***
        
        freq_options = ["Mensile", "Bimestrale", "Trimestrale", "Quadrimestrale", "Semestrale", "Annuale"] # Aggiunti
        freq_columns = 2
        
        for i, freq in enumerate(freq_options):
            row = i // freq_columns
            col = i % freq_columns
            
            radio = ttk.Radiobutton(freq_frame, text=freq, 
                                   variable=self.frequency_var, value=freq)
            radio.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
        
        # Configura grid
        for i in range(freq_columns):
            freq_frame.columnconfigure(i, weight=1)
        
        # *** TASSO PERIODO v15 ***
        rate_frame = ttk.LabelFrame(scrollable_content_frame, 
                                   text="🎯 Tasso Periodo (NON Annuale)", 
                                   padding="15")
        rate_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Info tasso
        info_label = ttk.Label(rate_frame, 
                              text="ℹ️ Inserisci il tasso del periodo di pagamento (come sui siti finanziari)",
                              font=("Arial", 10, "italic"),
                              foreground="blue")
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        rate_input_frame = ttk.Frame(rate_frame)
        rate_input_frame.pack(fill=tk.X)
        
        ttk.Label(rate_input_frame, 
                 text="Tasso Periodo (%):", 
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        
        self.rate_var = tk.DoubleVar(value=self.default_rate)  # *** VALORE DAL CERTIFICATO ***
        self.rate_entry = ttk.Entry(rate_input_frame, textvariable=self.rate_var, 
                                   width=15, font=("Arial", 11))
        self.rate_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Esempio dinamico
        example_frame = ttk.Frame(rate_frame)
        example_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.example_label = ttk.Label(example_frame, 
                                      text="", 
                                      font=("Arial", 9), 
                                      foreground="gray")
        self.example_label.pack(anchor=tk.W)
        
        # Bind per aggiornamento esempio
        self.frequency_var.trace_add('write', self._update_example)
        self.rate_var.trace_add('write', self._update_example)
        
        # Aggiorna esempio iniziale
        self._update_example()
        
        # *** OPZIONI AVANZATE ***
        advanced_frame = ttk.LabelFrame(scrollable_content_frame, text="Opzioni Avanzate", padding="15")
        advanced_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Metodo calcolo
        method_frame = ttk.Frame(advanced_frame)
        method_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(method_frame, text="Metodo Calcolo:").pack(side=tk.LEFT)
        
        self.method_var = tk.StringVar(value="robust_v15")
        method_combo = ttk.Combobox(method_frame, textvariable=self.method_var,
                                   values=["robust_v15", "legacy"], 
                                   state="readonly", width=15)
        method_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Info metodo
        method_info = ttk.Label(advanced_frame,
                               text="• robust_v15: Gestione intelligente date (raccomandato)\n• legacy: Metodo tradizionale",
                               font=("Arial", 9),
                               foreground="gray")
        method_info.pack(anchor=tk.W)
        
        # --- Buttons are now in fixed_bottom_frame ---
        # Pack canvas and scrollbar into main_container
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        # Bottone Annulla
        cancel_button = ttk.Button(button_frame, # Reparented
                                  text="❌ Annulla", 
                                  command=self._cancel,
                                  width=15)
        cancel_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Bottone Calcola
        calc_button = ttk.Button(button_frame, # Reparented
                                text="🧮 Calcola Date v15", 
                                command=self._calculate_dates_v15,
                                width=20)
        calc_button.pack(side=tk.RIGHT)
        
        # Bottone Preview
        preview_button = ttk.Button(button_frame, # Reparented
                                   text="👁️ Anteprima", 
                                   command=self._preview_calculation,
                                   width=15)
        preview_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Focus su rate entry
        self.rate_entry.focus()
    
    def _update_example(self, *args):
        """Aggiorna esempio dinamicamente"""
        try:
            frequency = self.frequency_var.get()
            period_rate = self.rate_var.get()
            
            # Calcola tasso annuo
            freq_map = {
                "Mensile": 12,
                "Bimestrale": 6,
                "Trimestrale": 4,
                "Quadrimestrale": 3,
                "Semestrale": 2,
                "Annuale": 1
            }
            
            periods_per_year = freq_map.get(frequency, 4)
            annual_rate = period_rate * periods_per_year
            
            example_text = f"📊 Es: {frequency} {period_rate:.2f}% → Tasso Annuo {annual_rate:.2f}%"
            self.example_label.config(text=example_text)
            
        except:
            self.example_label.config(text="📊 Esempio: inserisci valori validi")
    
    def _preview_calculation(self):
        """*** NUOVO v15 *** - Anteprima calcolo senza salvare"""
        try:
            if not self.selected_certificate_id or self.selected_certificate_id not in self.configurations:
                messagebox.showwarning("Attenzione", "Nessun certificato selezionato")
                return
            
            # Parametri
            frequency = self.frequency_var.get()
            period_rate = self.rate_var.get() / 100
            
            cert_data = self.configurations[self.selected_certificate_id]
            
            # Parse date
            issue_date_str = cert_data.get('issue_date', '')
            maturity_date_str = cert_data.get('maturity_date', '')
            
            if isinstance(issue_date_str, str):
                issue_date = datetime.fromisoformat(issue_date_str)
            else:
                issue_date = issue_date_str
                
            if isinstance(maturity_date_str, str):
                maturity_date = datetime.fromisoformat(maturity_date_str)
            else:
                maturity_date = maturity_date_str
            
            # Calcola date con metodo robusto
            date_utils = DateCalculationUtils()
            coupon_dates = date_utils.calculate_coupon_dates_robust(
                issue_date, maturity_date, frequency
            )
            
            # Crea preview
            preview_text = f"ANTEPRIMA CALCOLO DATE v15\n{'='*50}\n\n"
            preview_text += f"Certificato: {cert_data.get('name', 'N/A')}\n"
            preview_text += f"Frequenza: {frequency}\n"
            preview_text += f"Tasso Periodo: {period_rate:.3f}%\n" # Display con 3 decimali
            preview_text += f"Date Generate: {len(coupon_dates)}\n\n"
            
            preview_text += "DATE CEDOLE:\n"
            for i, date in enumerate(coupon_dates[:10]):  # Prime 10
                preview_text += f"  {i+1:2d}. {date.strftime('%Y-%m-%d')}\n"
            
            if len(coupon_dates) > 10:
                preview_text += f"  ... e altre {len(coupon_dates)-10} date\n"
            
            # Mostra preview
            PreviewDialog(self.dialog, "Anteprima Calcolo Date", preview_text)
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore anteprima:\n{e}")
    
    def _calculate_dates_v15(self):
        """*** VERSIONE CORRETTA v15 *** - Calcolo date con gestione errori completa"""
        
        try:
            print(f"🧮 === INIZIO CALCOLO DATE v15 ===")
            
            # Validazione input
            if not self.selected_certificate_id:
                messagebox.showerror("Errore", "Nessun certificato selezionato")
                return
            
            if not self.selected_certificate_id: # This check is redundant if the dialog is opened from a selection
                messagebox.showerror("Errore", "Nessun certificato selezionato per il calcolo delle date.")
                return            
            
            if self.selected_certificate_id not in self.configurations:
                messagebox.showerror("Errore", f"Certificato {self.selected_certificate_id} non trovato")
                return
            
            # Parametri
            frequency = self.frequency_var.get()
            try:
                raw_period_rate_input = self.rate_var.get()
                # Aggiungi un avviso se l'input sembra essere un decimale invece di una percentuale
                if raw_period_rate_input > 0 and raw_period_rate_input < 0.1: # es. 0.007 inserito
                    response = messagebox.askyesno(
                        "Attenzione: Tasso Periodo Basso",
                        f"Hai inserito {raw_period_rate_input}%. Intendevi {raw_period_rate_input * 100:.3f}%?\n\n"
                        "Il campo 'Tasso Periodo (%)' si aspetta un valore come '0.67' per 0.67%.\n"
                        "Se hai inserito un valore decimale (es. 0.0067), il risultato sarà molto piccolo.\n\n"
                        "Vuoi continuare con il valore inserito (che verrà diviso per 100)?\n"
                        "Clicca 'No' per modificare il valore."
                    )
                    if not response:
                        return # L'utente vuole modificare il valore

                period_rate = raw_period_rate_input / 100.0  # Converti in decimale
            except (ValueError, tk.TclError):
                messagebox.showerror("Errore", "Tasso periodo deve essere un numero")
                return
            
            if period_rate <= 0 or period_rate > 1:
                messagebox.showerror("Errore", "Tasso periodo deve essere tra 0% e 100%")
                return
            
            method = self.method_var.get()
            
            print(f"   Frequency: {frequency}")
            print(f"   Period rate: {period_rate:.4f}")
            print(f"   Method: {method}")
            
            # Dati certificato
            cert_data = self.configurations[self.selected_certificate_id]
            
            # Parse date con gestione errori
            try:
                issue_date_str = cert_data.get('issue_date', '')
                maturity_date_str = cert_data.get('maturity_date', '')
                
                if isinstance(issue_date_str, str):
                    issue_date = datetime.fromisoformat(issue_date_str)
                else:
                    issue_date = issue_date_str
                    
                if isinstance(maturity_date_str, str):
                    maturity_date = datetime.fromisoformat(maturity_date_str)
                else:
                    maturity_date = maturity_date_str
                
                print(f"   Issue: {issue_date.strftime('%Y-%m-%d')}")
                print(f"   Maturity: {maturity_date.strftime('%Y-%m-%d')}")
                
            except Exception as date_error:
                messagebox.showerror("Errore", f"Errore parsing date certificato:\n{date_error}")
                return
            
            # *** CALCOLO ROBUSTO v15 ***
            try:
                if method == "robust_v15":
                    date_utils = DateCalculationUtils()
                    coupon_dates = date_utils.calculate_coupon_dates_robust(
                        issue_date, maturity_date, frequency
                    )
                else:
                    # Metodo legacy (fallback)
                    coupon_dates = self._calculate_dates_legacy(issue_date, maturity_date, frequency)
                
                print(f"   ✅ Calcolate {len(coupon_dates)} date cedole")
                
            except Exception as calc_error:
                print(f"   ❌ Errore calcolo date: {calc_error}")
                messagebox.showerror("Errore Calcolo", 
                                   f"Errore nel calcolo date cedole:\n{calc_error}")
                return
            
            # Crea array rates e autocall
            coupon_rates = [period_rate] * len(coupon_dates)
            autocall_levels = [1.0] * len(coupon_dates)  # Default 100%
            
            # Calcola tasso annuo equivalente
            frequency_map = {
                "Mensile": 12, "Bimestrale": 6, "Trimestrale": 4, "Quadrimestrale": 3,
                "Semestrale": 2, "Annuale": 1
            }
            periods_per_year = frequency_map.get(frequency, 4)
            annual_equivalent = period_rate * periods_per_year
            
            # *** RISULTATO COMPLETO v15 ***
           

            self.result = {
                'coupon_dates': [d.isoformat() for d in coupon_dates],
                'coupon_rates': coupon_rates,
                'autocall_levels': autocall_levels,
                'coupon_frequency': frequency,
                'period_rate': period_rate,
                'period_rate_percent': period_rate * 100,
                'annual_equivalent_rate': annual_equivalent,
                'calculation_method': method,
                'calculation_version': 'v15',
                'calculation_timestamp': datetime.now().isoformat()
            }
            
            print(f"🧮 === CALCOLO DATE v15 COMPLETATO ===")
            print(f"   Risultato impostato: {self.result is not None}")
            print(f"   Date generate: {len(coupon_dates)}")
            print(f"   Tasso periodo: {period_rate * 100:.3f}%") # Display con 3 decimali
            print(f"   Tasso annuo equivalente: {annual_equivalent * 100:.3f}%") # Display con 3 decimali
            
            # Feedback all'utente
            messagebox.showinfo("Calcolo Completato v15", 
                              f"✅ Calcolate {len(coupon_dates)} date cedole\n\n"
                              f"Frequenza: {frequency}\n"
                              f"Tasso Periodo: {period_rate * 100:.3f}%\n"
                              f"Tasso Annuo Equivalente: {annual_equivalent * 100:.3f}%\n"
                              f"Metodo: {method}")
            
            # Chiudi dialog
            self.dialog.destroy()
            
        except Exception as e:
            print(f"🧮 === ERRORE CALCOLO DATE v15 ===")
            print(f"❌ Errore: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Errore", f"Errore durante il calcolo:\n{e}")
    
    def _calculate_dates_legacy(self, issue_date, maturity_date, frequency):
        """Metodo legacy per calcolo date (fallback)"""
        
        months_map = {
            "Mensile": 1, "Bimestrale": 2, "Trimestrale": 3, "Quadrimestrale": 4, # Aggiunti
            "Semestrale": 6, "Annuale": 12
        }
        
        months_inc = months_map.get(frequency, 3)
        coupon_dates = []
        
        # Semplice incremento mensile
        current_date = issue_date
        month = current_date.month + months_inc
        year = current_date.year
        day = current_date.day
        
        while year < maturity_date.year or (year == maturity_date.year and month <= maturity_date.month):
            if month > 12:
                year += (month - 1) // 12
                month = ((month - 1) % 12) + 1
            
            try:
                next_date = datetime(year, month, day)
                if next_date <= maturity_date:
                    coupon_dates.append(next_date)
                else:
                    break
            except ValueError:
                # Giorno non esiste, usa ultimo giorno del mese
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                next_date = datetime(year, month, min(day, last_day))
                if next_date <= maturity_date:
                    coupon_dates.append(next_date)
                else:
                    break
            
            month += months_inc
        
        # Aggiungi maturity se non presente
        if not coupon_dates or coupon_dates[-1] != maturity_date:
            coupon_dates.append(maturity_date)
        
        return coupon_dates
    
    def _cancel(self):
        """Annulla dialog"""
        print("❌ Dialog calcolo date v15 annullato")
        self.result = None
        self.dialog.destroy()


class PreviewDialog:
    """Dialog per anteprima risultati"""
    
    def __init__(self, parent, title, content):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text area con scroll
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_area = tk.Text(text_frame, wrap=tk.WORD, font=("Courier", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area.insert(1.0, content)
        text_area.config(state=tk.DISABLED)  # Read-only
        
        # Chiudi
        ttk.Button(main_frame, text="Chiudi", 
                  command=self.dialog.destroy).pack(pady=(10, 0))


# ========================================
# ESEMPIO INTEGRAZIONE CON GUI ESISTENTE
# ========================================

def integrate_with_fixed_gui_v14():
    """*** ESEMPIO *** - Come integrare con fixed_gui_manager_v14.py"""
    
    print("🔗 Integrazione Enhanced Certificate Manager v15 con GUI v14")
    
    # Il tuo GUI v14 può usare il manager enhanced così:
    
    # 1. Inizializza manager enhanced
    enhanced_manager = EnhancedCertificateManagerV15()
    
    # 2. Sostituisce metodo calcolo date auto nel GUI
    def new_auto_calculate_dates(gui_self):
        """Nuovo metodo per fixed_gui_manager_v14.py"""
        
        selection = gui_self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un certificato")
            return
        
        cert_id = gui_self.tree.item(selection[0])['values'][0]
        
        # *** USA DIALOG v15 ***
        dialog = CalculoDateAutoDialogV15(
            gui_self.root, 
            cert_id, 
            gui_self.certificates  # Passa configurazioni esistenti
        )
        
        if dialog.result:
            # Aggiorna certificato con date calcolate
            gui_self.certificates[cert_id].update({
                'coupon_dates': dialog.result['coupon_dates'],
                'coupon_rates': dialog.result['coupon_rates'],
                'autocall_levels': dialog.result['autocall_levels'],
                'coupon_frequency': dialog.result['coupon_frequency']
            })
            
            # Salva
            gui_self._save_certificates()
            gui_self._refresh_certificate_list()
            gui_self._display_certificate_details(cert_id)
            
            messagebox.showinfo("Successo v15", 
                              f"Date calcolate con metodo v15 per {cert_id}!")
    
    # 3. Sostituisce metodo nel GUI
    # gui._auto_calculate_dates = new_auto_calculate_dates
    
    print("✅ Integrazione pronta - sostituisci _auto_calculate_dates nel GUI")
    
    return enhanced_manager

# ========================================
# MAIN & TESTING
# ========================================

def test_enhanced_certificate_manager_v15():
    """Test completo Enhanced Certificate Manager v15"""
    
    print("\n🧪 TEST ENHANCED CERTIFICATE MANAGER v15")
    print("="*60)
    
    try:
        # 1. Inizializza manager
        print("1. Inizializzazione manager v15...")
        manager = EnhancedCertificateManagerV15()
        
        # 2. Test aggiunta certificato con yahoo_ticker
        print("2. Test aggiunta certificato con yahoo_ticker...")
        
        test_config = {
            'isin': 'TEST123456789',
            'name': 'Test Certificate v15',
            'certificate_type': 'cash_collect',
            'issuer': 'Test Bank',
            'yahoo_ticker': 'TEST.MI',  # *** TEST YAHOO_TICKER ***
            'underlying_assets': ['TEST1.MI', 'TEST2.MI'],
            'issue_date': '2024-01-15',
            'maturity_date': '2029-01-15',
            'notional': 1000.0,
            'currency': 'EUR',
            'memory_feature': True,
            'auto_update_market_data': False,  # Evita call reali
            'current_spots': [100.0, 200.0],
            'volatilities': [0.25, 0.30],
            'risk_free_rate': 0.035,
            'coupon_rate': 0.025, # Aggiunto per test
            'coupon_dates': ['2024-04-15', '2024-07-15'], # Aggiunto per test
            'barrier_levels': {'capital': 0.65, 'coupon': 0.70}
        }
        
        enhanced_config = manager.add_certificate_from_dict_v15(
            'TEST123456789', test_config
        )
        
        # Verifica yahoo_ticker
        yahoo_ticker = getattr(enhanced_config.base_config, 'yahoo_ticker', None)
        assert yahoo_ticker == 'TEST.MI', f"Yahoo ticker non salvato: {yahoo_ticker}"
        print(f"   ✅ Yahoo ticker salvato: {yahoo_ticker}")
        
        # 3. Test calcolo date robusto
        print("3. Test calcolo date robusto...")
        
        result = manager.calculate_coupon_dates_for_certificate(
            'TEST123456789', 'Trimestrale', 0.025
        )
        
        assert len(result['coupon_dates']) > 0, "Nessuna data cedola generata"
        print(f"   ✅ Generate {len(result['coupon_dates'])} date cedole")
        
        # 4. Test stato in-life
        print("4. Test stato in-life...")
        
        manager.update_certificate_in_life_state_v15(
            'TEST123456789',
            valuation_date=datetime(2025, 6, 15),
            paid_coupons=['2024-01-15', '2024-04-15'],
            memory_coupons=['2024-07-15']
        )
        
        config = manager.configurations['TEST123456789']
        assert len(config.in_life_state.paid_coupons) == 2, "Paid coupons non salvate"
        assert len(config.in_life_state.memory_coupons_due) == 1, "Memory coupons non salvate"
        print(f"   ✅ Stato in-life aggiornato")
        
        # 5. Test lista dettagliata
        print("5. Test lista dettagliata...")
        
        df = manager.list_certificates_detailed_v15()
        assert len(df) > 0, "Lista vuota"
        assert 'Yahoo Ticker' in df.columns, "Colonna Yahoo Ticker mancante"
        print(f"   ✅ Lista dettagliata: {len(df)} certificati")
        
        # 6. Test serializzazione/deserializzazione
        print("6. Test save/load...")
        
        # Forza salvataggio
        manager._save_configurations()
        
        # Crea nuovo manager e verifica caricamento
        manager2 = EnhancedCertificateManagerV15(manager.config_dir)
        
        assert 'TEST123456789' in manager2.configurations, "Certificato non caricato"
        
        config2 = manager2.configurations['TEST123456789']
        yahoo_ticker2 = getattr(config2.base_config, 'yahoo_ticker', None)
        assert yahoo_ticker2 == 'TEST.MI', f"Yahoo ticker non preservato: {yahoo_ticker2}"
        
        print(f"   ✅ Certificato caricato con yahoo_ticker: {yahoo_ticker2}")
        
        print("\n🎉 TUTTI I TEST v15 PASSATI!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test v15 fallito: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("ENHANCED CERTIFICATE MANAGER - VERSIONE CORRETTA v15")
    print("Sistema completo con tutte le correzioni integrate")
    print("="*70)
    
    # Test sistema
    success = test_enhanced_certificate_manager_v15()
    
    if success:
        print("\n✅ ENHANCED CERTIFICATE MANAGER v15 PRONTO!")
        print("\nCORREZIONI INTEGRATE:")
        print("✅ yahoo_ticker opzionale supportato")
        print("✅ Fix errore 'day out of range' nel calcolo date")
        print("✅ Dimensioni finestre calcolo date corrette")
        print("✅ Valori default caricati dal certificato selezionato")
        print("✅ Gestione robusta errori Yahoo Finance")
        print("✅ Validazione completa dati input")
        print("✅ Backward compatibility con configurazioni esistenti")
        
        print("\n🔗 INTEGRAZIONE CON GUI v14:")
        print("# Sostituisci _auto_calculate_dates nel tuo GUI v14")
        print("enhanced_manager = EnhancedCertificateManagerV15()")
        print("# Usa CalculoDateAutoDialogV15 invece del dialog esistente")
    
    else:
        print("\n❌ ERRORI NEL SISTEMA v15")