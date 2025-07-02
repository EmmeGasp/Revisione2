# ==========================================================
# RIEPILOGO CONTENUTO FILE:
# - Classi: CertificateConfigManager, CertificateTemplates, EnhancedCertificateSystem
# - Funzioni: setup_user_certificates, test_enhanced_system
# ==========================================================

# ========================================
# CERTIFICATE MANAGER - GESTIONE SENZA DATABASE
# Sistema per gestire multiple configurazioni certificate
# ========================================

"""
SOLUZIONE AL PROBLEMA CONFIGURAZIONI:

❌ PROBLEMA: Ogni volta devi ricreare RealCertificateConfig
✅ SOLUZIONE: Certificate Manager con configurazioni predefinite

CARATTERISTICHE:
- Salva configurazioni in file JSON
- Template per diversi tipi di certificati
- Import/Export configurazioni
- Portfolio management semplificato
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from pathlib import Path

# Import dal sistema esistente
from app.utils.real_certificate_integration import (
    RealCertificateConfig, IntegratedCertificateSystem,
    RealCertificateImporter
)

class CertificateConfigManager:
    """Gestore configurazioni certificati senza database"""
    
    def __init__(self, config_dir="D:/Doc/File python/configs/"): #DA VERIFICARE
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.configurations = {}
        self.portfolio_configs = {}
        
        # File di persistenza
        self.config_file = self.config_dir / "certificates.json"
        self.portfolio_file = self.config_dir / "portfolios.json"
        
        # Carica configurazioni esistenti
        self._load_configurations()
        
        print(f"📁 Certificate Config Manager inizializzato")
        print(f"   Directory configs: {self.config_dir}")
        print(f"   Certificati salvati: {len(self.configurations)}")
        print(f"   Portfolio salvati: {len(self.portfolio_configs)}")
    
    def create_certificate_config(self, cert_id: str, config_dict: Dict) -> RealCertificateConfig:
        """Crea configurazione certificato da dizionario"""
        
        # Converte date strings in datetime
        if isinstance(config_dict.get('issue_date'), str):
            config_dict['issue_date'] = datetime.fromisoformat(config_dict['issue_date'])
        if isinstance(config_dict.get('maturity_date'), str):
            config_dict['maturity_date'] = datetime.fromisoformat(config_dict['maturity_date'])
        
        # Converte coupon_dates
        if config_dict.get('coupon_dates'):
            config_dict['coupon_dates'] = [
                datetime.fromisoformat(date) if isinstance(date, str) else date
                for date in config_dict['coupon_dates']
            ]
        
        # Converte autocall_dates
        if config_dict.get('autocall_dates'):
            config_dict['autocall_dates'] = [
                datetime.fromisoformat(date) if isinstance(date, str) else date
                for date in config_dict['autocall_dates']
            ]
        
        # Converte correlations da lista a numpy array
        if config_dict.get('correlations') and isinstance(config_dict['correlations'], list):
            config_dict['correlations'] = np.array(config_dict['correlations'])
        
        # Crea configurazione
        config = RealCertificateConfig(**config_dict)
        
        # Salva nella cache
        self.configurations[cert_id] = config
        self._save_configurations()
        
        return config
    
    def save_certificate_config(self, cert_id: str, config: RealCertificateConfig):
        """Salva configurazione certificato"""
        self.configurations[cert_id] = config
        self._save_configurations()
        print(f"✅ Configurazione {cert_id} salvata")
    
    def get_certificate_config(self, cert_id: str) -> Optional[RealCertificateConfig]:
        """Recupera configurazione certificato"""
        return self.configurations.get(cert_id)
    
    def list_certificates(self) -> List[str]:
        """Lista tutti i certificati configurati"""
        return list(self.configurations.keys())
    
    def create_portfolio_config(self, portfolio_id: str, cert_ids: List[str], 
                              weights: List[float] = None, description: str = ""):
        """Crea configurazione portfolio"""
        
        if weights is None:
            weights = [1.0 / len(cert_ids)] * len(cert_ids)
        
        if len(cert_ids) != len(weights):
            raise ValueError("cert_ids e weights devono avere stessa lunghezza")
        
        # Verifica che tutti i certificati esistano
        missing_certs = [cid for cid in cert_ids if cid not in self.configurations]
        if missing_certs:
            raise ValueError(f"Certificati non trovati: {missing_certs}")
        
        portfolio_config = {
            'cert_ids': cert_ids,
            'weights': weights,
            'description': description,
            'created_date': datetime.now().isoformat()
        }
        
        self.portfolio_configs[portfolio_id] = portfolio_config
        self._save_portfolios()
        
        print(f"✅ Portfolio {portfolio_id} configurato con {len(cert_ids)} certificati")
        return portfolio_config
    
    def get_portfolio_config(self, portfolio_id: str) -> Optional[Dict]:
        """Recupera configurazione portfolio"""
        return self.portfolio_configs.get(portfolio_id)
    
    def list_portfolios(self) -> List[str]:
        """Lista tutti i portfolio configurati"""
        return list(self.portfolio_configs.keys())
    
    def _save_configurations(self):
        """Salva configurazioni su file JSON"""
        try:
            configs_dict = {}
            for cert_id, config in self.configurations.items():
                configs_dict[cert_id] = self._config_to_dict(config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(configs_dict, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Errore salvataggio configurazioni: {e}")
    
    def _save_portfolios(self):
        """Salva portfolio su file JSON"""
        try:
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio_configs, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Errore salvataggio portfolio: {e}")
    
    def _load_configurations(self):
        """Carica configurazioni da file JSON"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    configs_dict = json.load(f)
                
                for cert_id, config_dict in configs_dict.items():
                    try:
                        config = self.create_certificate_config(cert_id, config_dict)
                        # Non ri-salvare (evita loop)
                        self.configurations[cert_id] = config
                    except Exception as e:
                        print(f"⚠️  Errore caricamento config {cert_id}: {e}")
            
            if self.portfolio_file.exists():
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    self.portfolio_configs = json.load(f)
                    
        except Exception as e:
            print(f"⚠️  Errore caricamento configurazioni: {e}")
    
    def _config_to_dict(self, config: RealCertificateConfig) -> Dict:
        """Converte RealCertificateConfig in dizionario serializzabile"""
        config_dict = config.__dict__.copy()
        
        # Converte datetime in string
        for key, value in config_dict.items():
            if isinstance(value, datetime):
                config_dict[key] = value.isoformat()
            elif isinstance(value, list) and value and isinstance(value[0], datetime):
                config_dict[key] = [date.isoformat() for date in value]
            elif isinstance(value, np.ndarray):
                config_dict[key] = value.tolist()
        
        return config_dict

# ========================================
# TEMPLATE CONFIGURAZIONI PREDEFINITE
# ========================================

class CertificateTemplates:
    """Template predefiniti per diversi tipi di certificati"""
    
    @staticmethod
    def cash_collect_template():
        """Template per certificato Cash Collect"""
        return {
            'certificate_type': 'cash_collect',
            'currency': 'EUR',
            'memory_feature': True,
            'coupon_rates': [0.025] * 20,  # 2.5% trimestrale per 5 anni
            'autocall_levels': [1.0] * 20,  # Autocall al 100%
            'barrier_levels': { 
                'capital': 0.65,
                'coupon': 0.70
            },
            'risk_free_rate': 0.035,
            'dividend_yields': [0.04, 0.05, 0.03]
        }
    
    @staticmethod
    def express_template():
        """Template per certificato Express"""
        return {
            'certificate_type': 'express',
            'currency': 'EUR',
            'memory_feature': True,
            'coupon_rates': [0.08] * 5,  # 8% annuale per 5 anni
            'autocall_levels': [1.0] * 5,  # Autocall al 100%
            'barrier_levels': {'capital': 0.65},
            'risk_free_rate': 0.035
        }
    
    @staticmethod
    def phoenix_template():
        """Template per certificato Phoenix"""
        return {
            'certificate_type': 'phoenix',
            'currency': 'EUR',
            'memory_feature': True,
            'coupon_rates': [0.09] * 6,  # 9% annuale per 6 anni
            'barrier_levels': {
                'coupon': 0.70,
                'capital': 0.60
            },
            'risk_free_rate': 0.035
        }

# ========================================
# SISTEMA INTEGRATO CON CONFIG MANAGER
# ========================================

class EnhancedCertificateSystem:
    """Sistema certificati con gestione configurazioni integrate"""
    
    def __init__(self, excel_output_path="D:/Doc/File python/", 
                 config_dir="D:/Doc/File python/configs/"): #DA VERIFICARE
        
        self.config_manager = CertificateConfigManager(config_dir)
        self.integrated_system = IntegratedCertificateSystem(excel_output_path)
        
        print("🚀 Enhanced Certificate System inizializzato")
    
    def quick_add_certificate(self, cert_id: str, template_type: str, 
                            custom_params: Dict) -> RealCertificateConfig:
        """Aggiunge certificato rapidamente usando template"""
        
        # Ottieni template
        templates = {
            'cash_collect': CertificateTemplates.cash_collect_template(),
            'express': CertificateTemplates.express_template(),
            'phoenix': CertificateTemplates.phoenix_template()
        }
        
        if template_type not in templates:
            raise ValueError(f"Template non supportato: {template_type}")
        
        # Unisci template con parametri custom
        config_dict = templates[template_type].copy()
        config_dict.update(custom_params)
        
        # Crea configurazione
        config = self.config_manager.create_certificate_config(cert_id, config_dict)
        
        print(f"✅ Certificato {cert_id} aggiunto (template: {template_type})")
        return config
    
    def process_saved_certificate(self, cert_id: str, create_excel=True):
        """Processa certificato già salvato"""
        
        config = self.config_manager.get_certificate_config(cert_id)
        if not config:
            raise ValueError(f"Certificato {cert_id} non trovato nelle configurazioni")
        
        return self.integrated_system.process_real_certificate(
            config, create_excel_report=create_excel
        )
    
    def create_and_process_portfolio(self, portfolio_id: str):
        """Crea e processa portfolio salvato"""
        
        portfolio_config = self.config_manager.get_portfolio_config(portfolio_id)
        if not portfolio_config:
            raise ValueError(f"Portfolio {portfolio_id} non trovato")
        
        # Ottieni configurazioni certificati
        cert_configs = []
        for cert_id in portfolio_config['cert_ids']:
            config = self.config_manager.get_certificate_config(cert_id)
            if not config:
                raise ValueError(f"Certificato {cert_id} non trovato")
            cert_configs.append(config)
        
        # Processa portfolio
        return self.integrated_system.create_multi_certificate_portfolio(
            cert_configs, portfolio_config['weights']
        )
    
    def list_all(self):
        """Lista tutti i certificati e portfolio"""
        print("\n📋 CERTIFICATI CONFIGURATI:")
        for cert_id in self.config_manager.list_certificates():
            config = self.config_manager.get_certificate_config(cert_id)
            print(f"   {cert_id}: {config.name} ({config.certificate_type})")
        
        print("\n📊 PORTFOLIO CONFIGURATI:")
        for portfolio_id in self.config_manager.list_portfolios():
            portfolio = self.config_manager.get_portfolio_config(portfolio_id)
            print(f"   {portfolio_id}: {len(portfolio['cert_ids'])} certificati")

# ========================================
# ESEMPIO PRATICO - RICREA I TUOI CERTIFICATI
# ========================================

def setup_user_certificates():
    """Setup certificati dell'utente - ESEMPIO COMPLETO"""
    
    print("🔧 Setup certificati utente...")
    
    # Inizializza sistema
    system = EnhancedCertificateSystem()
    
    # 1. CERTIFICATO DE000VG6DRR5 (il tuo Cash Collect)
    de000vg6drr5_params = {
        'isin': 'DE000VG6DRR5',
        'name': 'Cash Collect Banking Stocks',
        'issuer': 'Vontobel',
        'underlying_assets': ['BMPS.MI', 'BAMI.MI', 'UCG.MI'],  # Tue correzioni
        'issue_date': datetime(2023, 6, 15),
        'maturity_date': datetime(2028, 6, 15),
        'notional': 1000.0,
        
        # Cedole trimestrali
        'coupon_dates': [
            # Anno 1
            datetime(2023, 9, 15), datetime(2023, 12, 15), 
            datetime(2024, 3, 15), datetime(2024, 6, 15),
            # Anno 2
            datetime(2024, 9, 15), datetime(2024, 12, 15),
            datetime(2025, 3, 15), datetime(2025, 6, 15),
            # Anno 3
             datetime(2025, 9, 15), datetime(2025, 12, 15),
            datetime(2026, 3, 15), datetime(2026, 6, 15),
            # Anno 4
            datetime(2026, 9, 15), datetime(2026, 12, 15),
            datetime(2027, 3, 15), datetime(2027, 6, 15),
            # Anno 5
            datetime(2027, 9, 15), datetime(2027, 12, 15),  
             datetime(2028, 3, 15), datetime(2028, 6, 15)
        ],
        
        # Market data correnti (AGGIORNA CON I TUOI DATI REALI)
        'current_spots': [2.85, 4.20, 18.50],  # BMPS, BAMI, UCG
        'volatilities': [0.35, 0.32, 0.30],    # Volatilità banche italiane
        'correlations': [
            [1.00, 0.70, 0.65],
            [0.70, 1.00, 0.60],
            [0.65, 0.60, 1.00]
        ]
    }
    
    config1 = system.quick_add_certificate(
        'DE000VG6DRR5', 'cash_collect', de000vg6drr5_params
    )
    
    # 2. SECONDO CERTIFICATO (esempio Express)
    express_params = {
        'isin': 'XS2675104231',
        'name': 'Capitale protetto Digital memory',
        'issuer': 'Intesa Sanpaolo',
        'underlying_assets': ['^STOXX50E', '^GSPC', '^N225'],
        'issue_date': datetime(2023, 9, 29),
        'maturity_date': datetime(2030, 9, 30),
        'notional': 1000.0,
        'coupon_dates': [
            datetime(2024, 9, 24), datetime(2025, 9, 24),
            datetime(2026, 9, 24), datetime(2027, 9, 24),
            datetime(2028, 9, 24)
        ],
        'current_spots': [5427.57, 6038.81, 38421.19],
        'volatilities': [0.25, 0.28, 0.22]
    }
    
    config2 = system.quick_add_certificate(
        'XS2675104231', 'express', express_params
    )
    
    # 3. CREA PORTFOLIO
    system.config_manager.create_portfolio_config(
        'PORTFOLIO_PRINCIPALE',
        ['DE000VG6DRR5', 'XS2675104231'],
        [0.60, 0.40]  # 60% cash collect, 40% express
    )
    
    print("✅ Setup completato!")
    system.list_all()
    
    return system

# ========================================
# TESTING SISTEMA COMPLETO
# ========================================

def test_enhanced_system():
    """Test sistema enhanced completo"""
    
    print("\n🧪 TEST ENHANCED SYSTEM")
    print("="*40)
    
    try:
        # Setup certificati
        system = setup_user_certificates()
        
        # Test 1: Processa certificato singolo
        print("\n1. Test processo certificato singolo...")
        cert, results = system.process_saved_certificate('DE000VG6DRR5')
        print(f"   ✅ {cert.specs.name} processato")
        
        # Test 2: Processa portfolio
        print("\n2. Test processo portfolio...")
        certificates, portfolio_results = system.create_and_process_portfolio('PORTFOLIO_PRINCIPALE')
        print(f"   ✅ Portfolio con {len(certificates)} certificati processato")
        
        print("\n🎉 ENHANCED SYSTEM TEST COMPLETATO!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test enhanced system fallito: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("CERTIFICATE MANAGER - GESTIONE SENZA DATABASE")
    print("="*60)
    
    success = test_enhanced_system()
    
    if success:
        print("\n✅ SISTEMA ENHANCED PRONTO!")
        print("\nCOME USARE:")
        print("1. system = setup_user_certificates()  # Setup iniziale")
        print("2. system.process_saved_certificate('DE000VG6DRR5')  # Singolo")
        print("3. system.create_and_process_portfolio('PORTFOLIO_PRINCIPALE')  # Portfolio")
    else:
        print("\n❌ ERRORI NEL SISTEMA ENHANCED")
 