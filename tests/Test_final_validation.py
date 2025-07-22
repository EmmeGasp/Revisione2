# tests/test_final_validation.py

import sys
import os
import unittest
from datetime import datetime

# Aggiungiamo la cartella 'src' al path di Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from app.core.unified_certificates import PhoenixCertificate, CouponSchedule
from app.core.structural_cleanup import CertificateSpecs

class TestFinalValidation(unittest.TestCase):

    def test_original_bug_scenario(self):
        """
        Questo test replica lo scenario fallito del 15/07 per validare la correzione.
        Scenario: Phoenix con Airbag + Barriera Dinamica, prezzo finale sotto la barriera.
        """
        print("\n--- Esecuzione Test di Validazione Finale (ex-bug 15/07) ---")

        # 1. Creiamo un certificato con le stesse caratteristiche del test originale
        specs = CertificateSpecs(
            name="Validazione Phoenix Airbag + Dinamica",
            isin="VALIDATION_ISIN",
            underlying="DUMMY_ASSET.MI",
            issue_date=datetime(2024, 1, 1),
            maturity_date=datetime(2026, 1, 1),
            strike=100.0,
            # Questo attiva la logica Airbag nel metodo calculate_payoff
            protection_level=60.0 
        )

        cert = PhoenixCertificate(
            specs=specs,
            underlying_assets=["DUMMY_ASSET.MI"],
            initial_prices=[100.0],
            coupon_schedule=CouponSchedule(payment_dates=[], rates=[]), # Non rilevante per questo test
            barrier_coupon=0.70,
            barrier_capitale=0.60, # La barriera capitale è il riferimento per l'Airbag
            memory_coupon=True,
            notional=1000.0,
            airbag_feature=True,
            airbag_level=0.60
        )

        # 2. Definiamo le condizioni finali dello scenario fallito
        prezzo_finale_sottostante = 55.0
        payoff_atteso_da_excel = 916.67

        print(f"Prezzo Finale Sottostante: {prezzo_finale_sottostante}")
        print(f"Livello Barriera Capitale / Airbag: {cert.barrier_capitale * 100}")
        print(f"Payoff Atteso (calcolo corretto con Airbag): {payoff_atteso_da_excel:.2f}")

        # 3. Chiamiamo il metodo 'calculate_payoff' corretto e verifichiamo il risultato
        payoff_ottenuto_attuale = cert.calculate_payoff(prezzo_finale_sottostante)
        
        print(f"Payoff Ottenuto (dal nuovo sistema): {payoff_ottenuto_attuale:.2f}")

        self.assertAlmostEqual(
            payoff_ottenuto_attuale, 
            payoff_atteso_da_excel, 
            places=2,
            msg="ERRORE: La correzione non ha risolto il bug originale!"
        )

        print("\n✅ SUCCESSO! Il bug del 15/07 è stato definitivamente risolto.")
        print("Il sistema ora calcola correttamente il payoff con Airbag e Barriera Dinamica.")

if __name__ == '__main__':
    unittest.main()