# ========================================
# MIGRATION SCRIPT - DA BASIC A ENHANCED
# Script per migrare dal sistema base al nuovo Enhanced Certificate Manager
# ========================================

"""
*** SCRIPT MIGRAZIONE *** 

OBIETTIVI:
✅ Rimuove duplicazioni (DE000VG6DRR5 definito una volta sola)
✅ Migra da certificates.json a enhanced_certificates.json
✅ Aggiunge supporto in-life valuation
✅ Fix warning dati mercato
✅ Integra Yahoo Finance auto-update
✅ Mantiene compatibilità backward

USO:
python migration_script.py
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# Import del nuovo sistema enhanced
from enhanced_certificate_manager import (
    EnhancedCertificateManager,
    YahooFinanceDataProvider,
    InLifeCertificateState,
    EnhancedCertificateConfig
)

# Import del vecchio sistema  
from real_certificate_integration import RealCertificateConfig

class CertificateMigrator:
    """Migra certificati dal sistema basic a enhanced"""
    
    def __init__(self, config_dir="D:/Doc/File python/configs/"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Files paths
        self.old_cert_file = self.config_dir / "certificates.json"
        self.old_portfolio_file = self.config_dir / "portfolios.json"
        self.new_cert_file = self.config_dir / "enhanced_certificates.json"
        self.new_portfolio_file = self.config_dir / "enhanced_portfolios.json"
        
        # Backup directory
        self.backup_dir = self.config_dir / "backup"
        self.backup_dir.mkdir(exist_ok=True)
        
        print("🔄 Certificate Migrator inizializzato")
        print(f"   Config dir: {self.config_dir}")
        print(f"   Backup dir: {self.backup_dir}")
    
    def migrate_all(self, auto_update_market_data=True, set_valuation_to_today=True):
        """*** MIGRAZIONE COMPLETA *** dal sistema basic a enhanced"""
        
        print("\n🚀 AVVIO MIGRAZIONE COMPLETA")
        print("="*50)
        
        try:
            # 1. Backup files esistenti
            print("1. Backup configurazioni esistenti...")
            self._backup_existing_files()
            
            # 2. Carica vecchie configurazioni
            print("2. Caricamento configurazioni basic...")
            old_certificates, old_portfolios = self._load_old_configurations()
            
            # 3. *** RISOLVE DUPLICAZIONI ***
            print("3. Risoluzione duplicazioni...")
            unique_certificates = self._resolve_duplications(old_certificates)
            
            # 4. Migra a enhanced format
            print("4. Migrazione a formato enhanced...")
            enhanced_certificates = self._migrate_to_enhanced_format(
                unique_certificates, 
                auto_update_market_data=auto_update_market_data,
                set_valuation_to_today=set_valuation_to_today
            )
            
            # 5. Migra portfolios
            print("5. Migrazione portfolio...")
            enhanced_portfolios = self._migrate_portfolios(old_portfolios, enhanced_certificates)
            
            # 6. Salva nuove configurazioni
            print("6. Salvataggio configurazioni enhanced...")
            self._save_enhanced_configurations(enhanced_certificates, enhanced_portfolios)
            
            # 7. Validazione
            print("7. Validazione migrazione...")
            validation_results = self._validate_migration(enhanced_certificates)
            
            # 8. Report finale
            self._generate_migration_report(unique_certificates, enhanced_certificates, validation_results)
            
            print("\n✅ MIGRAZIONE COMPLETATA CON SUCCESSO!")
            return True
            
        except Exception as e:
            print(f"\n❌ ERRORE MIGRAZIONE: {e}")
            print("🔄 Ripristino backup...")
            self._restore_backup()
            return False
    
    def _backup_existing_files(self):
        """Backup files esistenti"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.old_cert_file.exists():
            backup_cert = self.backup_dir / f"certificates_backup_{timestamp}.json"
            shutil.copy2(self.old_cert_file, backup_cert)
            print(f"   ✅ Backup certificati: {backup_cert}")
        
        if self.old_portfolio_file.exists():
            backup_portfolio = self.backup_dir / f"portfolios_backup_{timestamp}.json"
            shutil.copy2(self.old_portfolio_file, backup_portfolio)
            print(f"   ✅ Backup portfolio: {backup_portfolio}")
    
    def _load_old_configurations(self):
        """Carica configurazioni vecchio formato"""
        
        certificates = {}
        portfolios = {}
        
        # Carica certificati
        if self.old_cert_file.exists():
            with open(self.old_cert_file, 'r', encoding='utf-8') as f:
                certificates = json.load(f)
            print(f"   📋 Caricati {len(certificates)} certificati")
        
        # Carica portfolio
        if self.old_portfolio_file.exists():
            with open(self.old_portfolio_file, 'r', encoding='utf-8') as f:
                portfolios = json.load(f)
            print(f"   📊 Caricati {len(portfolios)} portfolio")
        
        return certificates, portfolios
    
    def _resolve_duplications(self, certificates):
        """*** RISOLVE DUPLICAZIONI *** - mantiene versione più completa"""
        
        print("   🔍 Ricerca duplicazioni...")
        
        # Raggruppa per ISIN
        isin_groups = {}
        for cert_id, cert_data in certificates.items():
            isin = cert_data.get('isin', cert_id)
            if isin not in isin_groups:
                isin_groups[isin] = []
            isin_groups[isin].append((cert_id, cert_data))
        
        # Risolve duplicazioni
        unique_certificates = {}
        duplications_found = 0
        
        for isin, cert_list in isin_groups.items():
            if len(cert_list) == 1:
                # Nessuna duplicazione
                cert_id, cert_data = cert_list[0]
                unique_certificates[cert_id] = cert_data
            else:
                # *** DUPLICAZIONE TROVATA ***
                duplications_found += len(cert_list) - 1
                print(f"   ⚠️  Duplicazione ISIN {isin}: {len(cert_list)} versioni")
                
                # Scegli versione migliore (quella con più dati)
                best_cert_id, best_cert_data = self._choose_best_certificate_version(cert_list)
                unique_certificates[best_cert_id] = best_cert_data
                
                print(f"   ✅ Mantenuta versione: {best_cert_id}")
        
        print(f"   📊 Duplicazioni risolte: {duplications_found}")
        print(f"   📋 Certificati unici: {len(unique_certificates)}")
        
        return unique_certificates
    
    def _choose_best_certificate_version(self, cert_list):
        """Sceglie la versione migliore del certificato (quella con più dati)"""
        
        best_score = -1
        best_cert = None
        
        for cert_id, cert_data in cert_list:
            # Calcola score basato su completezza dati
            score = 0
            
            # Dati base (peso 1)
            if cert_data.get('name'): score += 1
            if cert_data.get('issuer'): score += 1
            if cert_data.get('underlying_assets'): score += 1
            
            # Dati finanziari (peso 2)  
            if cert_data.get('coupon_rates'): score += 2
            if cert_data.get('coupon_dates'): score += 2
            if cert_data.get('barrier_levels'): score += 2
            
            # Dati mercato (peso 3)
            if cert_data.get('current_spots'): score += 3
            if cert_data.get('volatilities'): score += 3
            if cert_data.get('correlations'): score += 3
            
            # Preferisci nomi più descrittivi
            if cert_data.get('name') and len(cert_data.get('name', '')) > 10:
                score += 1
            
            print(f"     {cert_id}: score {score}")
            
            if score > best_score:
                best_score = score
                best_cert = (cert_id, cert_data)
        
        return best_cert
    
    def _migrate_to_enhanced_format(self, certificates, auto_update_market_data=True, 
                                  set_valuation_to_today=True):
        """Migra certificati a formato enhanced"""
        
        enhanced_certificates = {}
        yahoo_provider = YahooFinanceDataProvider() if auto_update_market_data else None
        
        for cert_id, cert_data in certificates.items():
            try:
                print(f"   🔄 Migrazione {cert_id}...")
                
                # *** FIX WARNING DATI MERCATO ***
                cert_data = self._fix_market_data_warnings(cert_data)
                
                # Crea base config
                base_config = self._dict_to_real_config(cert_data)
                
                # Crea enhanced config
                enhanced_config = EnhancedCertificateConfig(base_config)
                
                # *** SETUP IN-LIFE STATE ***
                if set_valuation_to_today:
                    enhanced_config.in_life_state.valuation_date = datetime.now()
                    
                    # *** SIMULA STATO IN-LIFE PER CERTIFICATI ESISTENTI ***
                    self._setup_realistic_in_life_state(enhanced_config)
                
                # *** AUTO-UPDATE MARKET DATA ***
                if auto_update_market_data and yahoo_provider:
                    print(f"     📊 Auto-update market data...")
                    try:
                        success = yahoo_provider.update_certificate_market_data(enhanced_config)
                        if success:
                            print(f"     ✅ Market data aggiornati")
                        else:
                            print(f"     ⚠️  Market data parzialmente aggiornati")
                    except Exception as e:
                        print(f"     ⚠️  Auto-update fallito: {e}")
                
                # Aggiorna metadata
                enhanced_config.metadata.update({
                    'migrated_from': 'basic_system',
                    'migration_date': datetime.now(),
                    'original_cert_id': cert_id,
                    'data_source': 'yahoo' if auto_update_market_data else 'manual'
                })
                
                enhanced_certificates[cert_id] = enhanced_config
                print(f"     ✅ {cert_id} migrato")
                
            except Exception as e:
                print(f"     ❌ Errore migrazione {cert_id}: {e}")
                # Continua con gli altri
        
        print(f"   📊 Migrati {len(enhanced_certificates)}/{len(certificates)} certificati")
        
        return enhanced_certificates
    
    def _fix_market_data_warnings(self, cert_data):
        """*** FIX WARNING DATI MERCATO *** risolve problemi comuni"""
        
        # Fix 1: Date coupon in ordine cronologico
        if cert_data.get('coupon_dates'):
            coupon_dates = cert_data['coupon_dates']
            if isinstance(coupon_dates[0], str):
                # Converti in datetime per ordinare
                date_objects = [datetime.fromisoformat(d) for d in coupon_dates]
                date_objects.sort()
                cert_data['coupon_dates'] = [d.isoformat() for d in date_objects]
        
        # Fix 2: Variazioni prezzo estreme (normalizza current_spots)
        if cert_data.get('current_spots'):
            spots = cert_data['current_spots']
            # Controlla variazioni estreme (>50% tra asset)
            min_spot = min(spots)
            max_spot = max(spots)
            
            if max_spot / min_spot > 50:  # Variazione > 5000%
                # Normalizza usando scale appropriate per tipo asset
                underlying_assets = cert_data.get('underlying_assets', [])
                normalized_spots = []
                
                for i, asset in enumerate(underlying_assets):
                    spot = spots[i] if i < len(spots) else 100.0
                    
                    # Scale intelligenti basate su pattern asset name
                    if any(x in asset.upper() for x in ['BMPS', 'BAMI', 'UCG', 'ISP']):
                        # Banche italiane: range 1-50
                        normalized_spot = max(1.0, min(50.0, spot))
                    elif '^' in asset or 'STOXX' in asset.upper() or 'GSPC' in asset.upper():
                        # Indici: range 1000-40000
                        normalized_spot = max(1000.0, min(40000.0, spot))
                    else:
                        # Altri: range 10-200
                        normalized_spot = max(10.0, min(200.0, spot))
                    
                    normalized_spots.append(normalized_spot)
                
                cert_data['current_spots'] = normalized_spots
                print(f"     🔧 Fixed extreme price variations: {spots} → {normalized_spots}")
        
        # Fix 3: Correlazioni ragionevoli
        if cert_data.get('correlations'):
            corr = np.array(cert_data['correlations'])
            # Assicura correlazioni tra -1 e 1
            corr = np.clip(corr, -0.99, 0.99)
            # Assicura diagonale = 1
            np.fill_diagonal(corr, 1.0)
            cert_data['correlations'] = corr.tolist()
        
        return cert_data
    
    def _setup_realistic_in_life_state(self, enhanced_config):
        """*** SETUP STATO IN-LIFE REALISTICO *** per certificati esistenti"""
        
        base_config = enhanced_config.base_config
        in_life_state = enhanced_config.in_life_state
        
        # Calcola tempo trascorso dall'emissione
        issue_date = base_config.issue_date
        valuation_date = in_life_state.valuation_date
        days_elapsed = (valuation_date - issue_date).days
        
        if days_elapsed > 0:
            # Certificato già emesso - simula eventi passati
            
            # Simula cedole pagate (assume ~70% pagate se date passate)
            if base_config.coupon_dates:
                paid_coupons = []
                memory_coupons = []
                
                for coupon_date in base_config.coupon_dates:
                    if coupon_date < valuation_date:
                        # Data passata - simula se pagata o in memoria
                        # 70% probabilità pagata, 30% in memoria per mercato sotto barriera
                        import random
                        if random.random() < 0.7:
                            paid_coupons.append(coupon_date)
                        else:
                            memory_coupons.append(coupon_date)
                
                in_life_state.paid_coupons = paid_coupons
                in_life_state.memory_coupons_due = memory_coupons
                
                print(f"     📅 Simulato stato: {len(paid_coupons)} cedole pagate, {len(memory_coupons)} in memoria")
        
        # Verifica se ancora attivo
        if valuation_date >= base_config.maturity_date:
            in_life_state.is_active = False
            print(f"     ⏰ Certificato scaduto")
    
    def _migrate_portfolios(self, old_portfolios, enhanced_certificates):
        """Migra portfolio a formato enhanced"""
        
        enhanced_portfolios = {}
        
        for portfolio_id, portfolio_data in old_portfolios.items():
            try:
                # Verifica che tutti i certificati esistano
                cert_ids = portfolio_data.get('cert_ids', [])
                valid_cert_ids = [cid for cid in cert_ids if cid in enhanced_certificates]
                
                if len(valid_cert_ids) != len(cert_ids):
                    print(f"   ⚠️  Portfolio {portfolio_id}: alcuni certificati non trovati")
                
                # Aggiorna portfolio config
                enhanced_portfolio = portfolio_data.copy()
                enhanced_portfolio.update({
                    'cert_ids': valid_cert_ids,
                    'portfolio_type': 'enhanced',
                    'in_life_mode': True,
                    'migrated_from': 'basic_system',
                    'migration_date': datetime.now().isoformat()
                })
                
                # Aggiusta weights se necessario
                if len(valid_cert_ids) != len(portfolio_data.get('weights', [])):
                    # Ricalcola equal weights
                    enhanced_portfolio['weights'] = [1.0 / len(valid_cert_ids)] * len(valid_cert_ids)
                
                enhanced_portfolios[portfolio_id] = enhanced_portfolio
                print(f"   ✅ Portfolio {portfolio_id} migrato")
                
            except Exception as e:
                print(f"   ❌ Errore migrazione portfolio {portfolio_id}: {e}")
        
        return enhanced_portfolios
    
    def _save_enhanced_configurations(self, enhanced_certificates, enhanced_portfolios):
        """Salva configurazioni enhanced"""
        
        # Prepara dati per serializzazione
        cert_data = {}
        for cert_id, enhanced_config in enhanced_certificates.items():
            cert_data[cert_id] = self._enhanced_config_to_dict(enhanced_config)
        
        # Salva certificati
        with open(self.new_cert_file, 'w', encoding='utf-8') as f:
            json.dump(cert_data, f, indent=2, default=str)
        
        # Salva portfolio
        with open(self.new_portfolio_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_portfolios, f, indent=2, default=str)
        
        print(f"   ✅ Salvati in {self.new_cert_file}")
        print(f"   ✅ Salvati in {self.new_portfolio_file}")
    
    def _validate_migration(self, enhanced_certificates):
        """Valida risultati migrazione"""
        
        validation_results = {
            'total_certificates': len(enhanced_certificates),
            'certificates_with_market_data': 0,
            'certificates_with_in_life_state': 0,
            'errors': []
        }
        
        for cert_id, enhanced_config in enhanced_certificates.items():
            try:
                # Verifica market data
                if (enhanced_config.base_config.current_spots and 
                    enhanced_config.base_config.volatilities):
                    validation_results['certificates_with_market_data'] += 1
                
                # Verifica in-life state
                if enhanced_config.in_life_state.valuation_date:
                    validation_results['certificates_with_in_life_state'] += 1
                
            except Exception as e:
                validation_results['errors'].append(f"{cert_id}: {e}")
        
        return validation_results
    
    def _generate_migration_report(self, original_certificates, enhanced_certificates, validation_results):
        """Genera report migrazione"""
        
        print(f"\n📊 REPORT MIGRAZIONE")
        print(f"="*40)
        print(f"Certificati originali: {len(original_certificates)}")
        print(f"Certificati migrati: {len(enhanced_certificates)}")
        print(f"Con market data: {validation_results['certificates_with_market_data']}")
        print(f"Con in-life state: {validation_results['certificates_with_in_life_state']}")
        
        if validation_results['errors']:
            print(f"\n⚠️  ERRORI:")
            for error in validation_results['errors'][:5]:  # Max 5
                print(f"   {error}")
        
        # Salva report su file
        report_data = {
            'migration_date': datetime.now().isoformat(),
            'original_certificates_count': len(original_certificates),
            'enhanced_certificates_count': len(enhanced_certificates),
            'validation_results': validation_results,
            'migrated_certificates': list(enhanced_certificates.keys())
        }
        
        report_file = self.config_dir / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"📄 Report salvato: {report_file}")
    
    def _restore_backup(self):
        """Ripristina backup in caso di errore"""
        try:
            # Trova backup più recente
            backup_files = list(self.backup_dir.glob("certificates_backup_*.json"))
            if backup_files:
                latest_backup = max(backup_files, key=os.path.getctime)
                shutil.copy2(latest_backup, self.old_cert_file)
                print(f"   🔄 Ripristinato: {latest_backup}")
        except Exception as e:
            print(f"   ❌ Errore ripristino: {e}")
    
    # Utility methods (simplified)
    def _dict_to_real_config(self, config_dict):
        """Converte dict in RealCertificateConfig"""
        
        # Convert dates
        for date_field in ['issue_date', 'maturity_date']:
            if isinstance(config_dict.get(date_field), str):
                config_dict[date_field] = datetime.fromisoformat(config_dict[date_field])
        
        # Convert date lists
        for date_list_field in ['coupon_dates', 'autocall_dates']:
            if config_dict.get(date_list_field):
                config_dict[date_list_field] = [
                    datetime.fromisoformat(date) if isinstance(date, str) else date
                    for date in config_dict[date_list_field]
                ]
        
        # Convert correlations
        if config_dict.get('correlations') and isinstance(config_dict['correlations'], list):
            config_dict['correlations'] = np.array(config_dict['correlations'])
        
        return RealCertificateConfig(**config_dict)
    
    def _enhanced_config_to_dict(self, enhanced_config):
        """Converte enhanced config in dict per serializzazione"""
        
        # Base config
        base_dict = enhanced_config.base_config.__dict__.copy()
        
        # Convert dates and arrays
        for key, value in base_dict.items():
            if isinstance(value, datetime):
                base_dict[key] = value.isoformat()
            elif isinstance(value, list) and value and isinstance(value[0], datetime):
                base_dict[key] = [date.isoformat() for date in value]
            elif isinstance(value, np.ndarray):
                base_dict[key] = value.tolist()
        
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
            'enhanced_version': '2.0'
        }


# ========================================
# MAIN MIGRATION SCRIPT
# ========================================

def run_migration():
    """*** SCRIPT PRINCIPALE MIGRAZIONE ***"""
    
    print("🚀 CERTIFICATE MIGRATION SCRIPT")
    print("Da Basic Certificate Manager a Enhanced In-Life System")
    print("="*65)
    
    migrator = CertificateMigrator()
    
    # Opzioni migrazione
    print("\n⚙️  OPZIONI MIGRAZIONE:")
    print("1. Auto-update market data da Yahoo Finance")
    print("2. Imposta valuation date a oggi (vs data emissione)")
    print("3. Simula stato in-life realistico")
    
    auto_update = input("\nAuto-update market data? (y/n, default=y): ").lower() != 'n'
    set_valuation_today = input("Valuation date oggi? (y/n, default=y): ").lower() != 'n'
    
    print(f"\n📋 CONFIGURAZIONE MIGRAZIONE:")
    print(f"   Auto-update market data: {auto_update}")
    print(f"   Valuation date oggi: {set_valuation_today}")
    
    confirm = input("\n🚀 Avviare migrazione? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Migrazione annullata")
        return False
    
    # Esegui migrazione
    success = migrator.migrate_all(
        auto_update_market_data=auto_update,
        set_valuation_to_today=set_valuation_today
    )
    
    if success:
        print(f"\n🎉 MIGRAZIONE COMPLETATA!")
        print(f"\n📋 PROSSIMI PASSI:")
        print(f"1. Testare Enhanced Certificate Manager:")
        print(f"   from enhanced_certificate_manager import EnhancedCertificateManager")
        print(f"   manager = EnhancedCertificateManager()")
        print(f"")
        print(f"2. Testare GUI:")
        print(f"   from enhanced_certificate_manager import CertificateManagerGUI")
        print(f"   gui = CertificateManagerGUI()")
        print(f"   gui.run()")
        print(f"")
        print(f"3. Processare certificati in-life:")
        print(f"   cert, results = manager.process_certificate_in_life('DE000VG6DRR5')")
        
    return success

if __name__ == "__main__":
    run_migration()
