# tests/test_risk_system_features.py

import sys
import os
import unittest
from datetime import datetime
import numpy as np

# --- INIZIO CORREZIONE PERCORSO ---
# Aggiungiamo la cartella 'src' al path di Python.
# Usiamo '..' per "risalire" dalla cartella /tests alla root del progetto
# e poi entrare in /src. Questo risolve il ModuleNotFoundError.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
# --- FINE CORREZIONE PERCORSO ---

# Ora gli import funzioneranno
from app.core.unified_certificates import PhoenixCertificate, CouponSchedule
from app.core.structural_cleanup import CertificateSpecs
from app.core.real_certificate_integration import RealCertificateConfig
from app.core.consolidated_risk_system import UnifiedRiskAnalyzer

class TestCombinedFeatures(unittest.TestCase):

# In tests/test_risk_system_features.py, sostituisci solo questa funzione

    # In tests/test_risk_system_features.py, sostituisci solo questa funzione

# In tests/test_risk_system_features.py, sostituisci solo questa funzione

# In tests/test_risk_system_features.py, sostituisci solo questa funzione

    def _create_test_certificate(self, name: str, dynamic_barrier: bool, airbag: bool) -> PhoenixCertificate:
        """
        Funzione helper per creare un certificato Phoenix con feature specifiche.
        *** VERSIONE FINALE CHE RISPETTA LA STRUTTURA DELLE CLASSI ***
        """
        # Parametri che vanno passati direttamente al certificato
        initial_prices_data = [100.0, 100.0]
        
        # Dizionario per la configurazione statica (RealCertificateConfig)
        base_config_dict = {
            'isin': f"ISIN_{name.replace(' ', '_').upper()}",
            'name': name,
            'certificate_type': 'phoenix',
            'issuer': 'Test Bank',
            'underlying_assets': ["ASSET_A.MI", "ASSET_B.MI"],
            'issue_date': datetime(2024, 1, 1),
            'maturity_date': datetime(2027, 1, 1),
            'coupon_dates': [datetime(2025, 1, 1), datetime(2026, 1, 1), datetime(2027, 1, 1)],
            'coupon_rates': [0.08, 0.08, 0.08],
            'notional': 1000.0,
            'dynamic_barrier_feature': dynamic_barrier,
            'dynamic_barrier_start_level': 0.70,
            'step_down_rate': 0.05,
            'dynamic_barrier_end_level': 0.60,
            'observation_delay_months': 12,
            'airbag_level': 0.60
        }
        base_config = RealCertificateConfig(**base_config_dict)
        
        # Creiamo il certificato
        cert = PhoenixCertificate(
            specs=CertificateSpecs(
                isin=base_config.isin,
                name=base_config.name,
                # AGGIUNTO IL CAMPO MANCANTE 'underlying'
                underlying=", ".join(base_config.underlying_assets),
                issue_date=base_config.issue_date,
                maturity_date=base_config.maturity_date,
                strike=100.0
            ),
            underlying_assets=base_config.underlying_assets,
            initial_prices=initial_prices_data,
            coupon_schedule=CouponSchedule(payment_dates=base_config.coupon_dates, rates=base_config.coupon_rates),
            barrier_coupon=0.70,
            barrier_capitale=0.70,
            memory_coupon=True,
            notional=base_config.notional,
            airbag_feature=airbag,
            airbag_level=base_config.airbag_level,
        )
        
        # Colleghiamo la configurazione base al certificato
        cert.base_config = base_config
        # Impostiamo i parametri di mercato
        cert.setup_market_parameters(
            spot_prices=[100.0, 100.0],
            volatilities=[0.30, 0.30],
            correlations=np.array([[1.0, 0.5], [0.5, 1.0]]),
            risk_free_rate=0.02,
            dividends=[0.0, 0.0]
        )
        
        # Aggiungiamo attributi che il risk analyzer si aspetta
        cert.dynamic_barrier_feature = dynamic_barrier
        
        return cert    
    def test_risk_reduction_with_features(self):
        """
        Verifica che l'aggiunta di Airbag e Barriera Dinamica riduca il rischio (VaR).
        """
        print("\n--- Test di Rischio Combinato: Airbag + Barriera Dinamica ---")
        
        # 1. Creiamo i tre certificati da confrontare
        cert_base = self._create_test_certificate("Base", dynamic_barrier=False, airbag=False)
        cert_airbag_only = self._create_test_certificate("Airbag Only", dynamic_barrier=False, airbag=True)
        cert_combined = self._create_test_certificate("Combined", dynamic_barrier=True, airbag=True)

        # 2. Inizializziamo l'analizzatore di rischio
        risk_analyzer = UnifiedRiskAnalyzer()

        # 3. Calcoliamo il rischio per ogni certificato
        print("\nAnalisi Rischio per Certificato BASE...")
        risk_base = risk_analyzer.analyze_certificate_risk(cert_base, n_simulations=5000)

        print("\nAnalisi Rischio per Certificato con solo AIRBAG...")
        risk_airbag_only = risk_analyzer.analyze_certificate_risk(cert_airbag_only, n_simulations=5000)
        
        print("\nAnalisi Rischio per Certificato COMBINATO (Airbag + Dinamica)...")
        risk_combined = risk_analyzer.analyze_certificate_risk(cert_combined, n_simulations=5000)

        # 4. Stampiamo e verifichiamo i risultati
        print("\n--- RISULTATI CONFRONTO RISCHIO (VaR 95%) ---")
        print(f"  - Certificato Base:              {risk_base.var_95: .2%}")
        print(f"  - Certificato con solo Airbag:   {risk_airbag_only.var_95: .2%}")
        print(f"  - Certificato Combinato:         {risk_combined.var_95: .2%}")
        print("-------------------------------------------------")
        
        # 5. Asserzioni: verifichiamo che il rischio diminuisca come atteso
        self.assertLess(risk_base.var_95, risk_airbag_only.var_95, "L'Airbag da solo non ha ridotto il rischio (VaR).")
        self.assertLessEqual(risk_airbag_only.var_95, risk_combined.var_95, "La barriera dinamica non ha ulteriormente ridotto o mantenuto il rischio.")
        
        print("\n✅ VERIFICA OK: Le feature riducono il rischio come atteso.")

if __name__ == '__main__':
    unittest.main()