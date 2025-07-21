# tests/test_airbag_dynamic_barrier.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from datetime import datetime

from src.app.core.unified_certificates import (
    UnifiedCertificateFactory,
    CertificateType,
    Barrier,
    BarrierType,
    CouponSchedule  # <-- Importiamo la classe che ci serve
)
from src.app.core.structural_cleanup import CertificateSpecs

class TestDynamicBarrierWithAirbag(unittest.TestCase):

    def test_definitive_scenario_with_all_params(self):
        """
        Test finale che usa oggetti Barrier e CouponSchedule corretti.
        """
        print("\n--- Esecuzione Test 5: Oggetti Corretti ---")

        cert_type = CertificateType.EXPRESS

        specs_object = CertificateSpecs(
            name="Certificato Airbag con Barriera Dinamica",
            isin="TEST_ISIN_05",
            underlying='DUMMY_ASSET.MI',
            issue_date=datetime(2024, 1, 1),
            maturity_date=datetime(2026, 1, 1),
            strike=100.0,
            barrier=90.0,
            protection_level=90.0
        )
        
        # Correzione del tipo di barriera, come da tua indicazione
        barrier_object = Barrier(level=90.0, type=BarrierType.EUROPEAN)

        # 1. Prepariamo i dati per le cedole
        raw_coupon_data = [(datetime(2025, 7, 17), 0.05)] # Tasso 5%
        coupon_dates = [date for date, rate in raw_coupon_data]
        coupon_rates = [rate for date, rate in raw_coupon_data]
        
        # 2. Creiamo l'oggetto CouponSchedule
        coupon_schedule_object = CouponSchedule(payment_dates=coupon_dates, rates=coupon_rates)

        factory_config = {
            'specs': specs_object,
            'underlying_assets': ['DUMMY_ASSET.MI'],
            'autocall_levels': [100.0],
            'autocall_dates': [datetime(2025, 1, 1)],
            'initial_prices': [100.0],
            'barrier': barrier_object,
            # Passiamo l'oggetto CouponSchedule
            'coupon_schedule': coupon_schedule_object
        }

        # 3. Chiamiamo la factory
        certificate_test_5 = UnifiedCertificateFactory.create_certificate(
            cert_type, **factory_config
        )

        # 4. SIMULAZIONE E VERIFICA
        final_price = 80.0
        face_value = 1000.0

        print(f"Prezzo finale del sottostante: {final_price}")
        print(f"Livello barriera: {certificate_test_5.barrier.level}")
        
        expected_payoff = (final_price / certificate_test_5.barrier.level) * face_value
        print(f"Payoff ATTESO (con Airbag): {expected_payoff:.2f}")

        actual_payoff = certificate_test_5.calculate_payoff(final_price)
        print(f"Payoff OTTENUTO dalla funzione: {actual_payoff:.2f}")

        self.assertAlmostEqual(actual_payoff, expected_payoff, places=2,
                               msg="ERRORE: Il payoff con Airbag è SBAGLIATO!")

        print("--- Test Eseguito ---")

if __name__ == '__main__':
    unittest.main()