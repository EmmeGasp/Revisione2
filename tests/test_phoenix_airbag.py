# tests/test_phoenix_airbag.py

import sys
import os
import unittest
from datetime import datetime

# Aggiunge la directory principale al path per permettere l'import dell'applicazione
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.core.unified_certificates import (
    UnifiedCertificateFactory,
    PhoenixCertificate,
    CertificateType,
    CouponSchedule
)
from src.app.core.structural_cleanup import CertificateSpecs

class TestPhoenixWithAirbag(unittest.TestCase):

    def _create_phoenix_certificate(self, airbag_enabled: bool) -> PhoenixCertificate:
        """Funzione helper per creare un certificato Phoenix di test."""
        
        protection = 70.0 if airbag_enabled else 0.0
        
        specs_object = CertificateSpecs(
            name=f"Phoenix Test (Airbag: {airbag_enabled})",
            isin=f"TEST_ISIN_PHOENIX_{'AIRBAG' if airbag_enabled else 'NO_AIRBAG'}",
            underlying='DUMMY_ASSET.MI',
            issue_date=datetime(2024, 1, 1),
            maturity_date=datetime(2026, 1, 1),
            strike=100.0,
            # Questo attiva la logica nel nuovo metodo calculate_payoff
            protection_level=protection 
        )

        coupon_schedule_object = CouponSchedule(
            payment_dates=[datetime(2025, 1, 1)], 
            rates=[0.05]
        )

        factory_config = {
            'specs': specs_object,
            'underlying_assets': ['DUMMY_ASSET.MI'],
            'initial_prices': [100.0],
            'coupon_schedule': coupon_schedule_object,
            'barrier_coupon': 0.75,
            'barrier_capitale': 0.70, # Barriera capitale al 70%
            'memory_coupon': True,
            'notional': 1000.0,
            # Parametro esplicito per la classe Phoenix
            'airbag_feature': airbag_enabled,
            'airbag_level': protection if airbag_enabled else None
        }

        certificate = UnifiedCertificateFactory.create_certificate(
            CertificateType.PHOENIX, **factory_config
        )
        return certificate

    def test_phoenix_payoff_WITH_airbag(self):
        """
        Testa il payoff di un Phoenix Certificate CON Airbag quando la barriera è violata.
        """
        print("\n--- Esecuzione Test Phoenix: CON AIRBAG ---")
        certificate = self._create_phoenix_certificate(airbag_enabled=True)
        
        # Dati per la simulazione
        final_price = 60.0  # Sotto la barriera del 70% (70.0)
        notional_value = certificate.notional
        strike_price = certificate.specs.strike
        barrier_price = strike_price * certificate.barrier_capitale

        print(f"Prezzo finale del sottostante: {final_price}")
        print(f"Strike Price: {strike_price}")
        print(f"Livello Barriera Capitale: {barrier_price}")
        print("La barriera è violata.")

        # Con l'airbag, il riferimento per la perdita è la barriera, non lo strike
        expected_payoff = (final_price / barrier_price) * notional_value
        print(f"Payoff ATTESO (con Airbag): ({final_price} / {barrier_price}) * {notional_value} = {expected_payoff:.2f}")

        actual_payoff = certificate.calculate_payoff(final_price)
        print(f"Payoff OTTENUTO dalla funzione: {actual_payoff:.2f}")

        self.assertAlmostEqual(actual_payoff, expected_payoff, places=2,
                               msg="ERRORE: Il payoff del Phoenix con Airbag è SBAGLIATO!")
        print("--- Test CON Airbag: PASSATO ---")

    def test_phoenix_payoff_WITHOUT_airbag(self):
        """
        Testa il payoff di un Phoenix Certificate SENZA Airbag quando la barriera è violata.
        """
        print("\n--- Esecuzione Test Phoenix: SENZA AIRBAG ---")
        certificate = self._create_phoenix_certificate(airbag_enabled=False)
        
        # Dati per la simulazione
        final_price = 60.0  # Sotto la barriera del 70% (70.0)
        notional_value = certificate.notional
        strike_price = certificate.specs.strike
        
        print(f"Prezzo finale del sottostante: {final_price}")
        print(f"Strike Price: {strike_price}")
        print(f"Livello Barriera Capitale: {strike_price * certificate.barrier_capitale}")
        print("La barriera è violata.")

        # Senza airbag, il riferimento per la perdita è lo strike price
        expected_payoff = (final_price / strike_price) * notional_value
        print(f"Payoff ATTESO (senza Airbag): ({final_price} / {strike_price}) * {notional_value} = {expected_payoff:.2f}")

        actual_payoff = certificate.calculate_payoff(final_price)
        print(f"Payoff OTTENUTO dalla funzione: {actual_payoff:.2f}")

        self.assertAlmostEqual(actual_payoff, expected_payoff, places=2,
                               msg="ERRORE: Il payoff del Phoenix senza Airbag è SBAGLIATO!")
        print("--- Test SENZA Airbag: PASSATO ---")

if __name__ == '__main__':
    unittest.main()