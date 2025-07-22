# analysis_airbag_simulation.py
import sys
import os

# --- INIZIO CORREZIONE PERCORSO ---
# Aggiungiamo la cartella 'src' al path di Python per trovare il modulo 'app'
# Questo risolve il ModuleNotFoundError
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './src')))
# --- FINE CORREZIONE PERCORSO ---

import unittest
from datetime import datetime, timedelta
import numpy as np

# Ora gli import funzioneranno
from app.core.unified_certificates import (
    ExpressCertificate, CertificateType, Barrier, BarrierType, CouponSchedule
)
from app.core.structural_cleanup import CertificateSpecs

def create_express_test_cert(airbag_enabled: bool) -> ExpressCertificate:
    """Funzione helper per creare un certificato Express di test."""
    
    protection = 70.0 if airbag_enabled else 0.0
    
    specs = CertificateSpecs(
        name=f"Express Test (Airbag: {airbag_enabled})",
        isin="ISIN_TEST_EXPRESS",
        underlying="MULTI_ASSET",
        issue_date=datetime(2024, 1, 1),
        maturity_date=datetime(2026, 1, 1),
        strike=100.0,
        protection_level=protection
    )
    
    coupon_schedule = CouponSchedule(
        payment_dates=[datetime(2025, 1, 1), datetime(2026, 1, 1)],
        rates=[0.05, 0.05]
    )
    
    barrier = Barrier(level=0.70, type=BarrierType.EUROPEAN)
    
    autocall_dates = [datetime(2025, 1, 1)]
    autocall_levels = [1.0]

    cert = ExpressCertificate(
        specs=specs,
        underlying_assets=["ASSET_A", "ASSET_B"],
        initial_prices=[100.0, 100.0],
        coupon_schedule=coupon_schedule,
        autocall_levels=autocall_levels,
        autocall_dates=autocall_dates,
        barrier=barrier,
        notional=1000.0,
        airbag_feature=airbag_enabled,
        airbag_level=barrier.level if airbag_enabled else None
    )
    
    # Parametri di mercato
    correlations = np.array([[1.0, 0.5], [0.5, 1.0]])
    cert.setup_market_parameters(
        spot_prices=[100.0, 100.0],
        volatilities=[0.3, 0.3], # Volatilità alta per vedere l'effetto
        correlations=correlations,
        risk_free_rate=0.01,
        dividends=[0.0, 0.0]
    )
    return cert

def run_analysis():
    """Esegue l'analisi comparativa."""
    
    print("--- Avvio analisi comparativa simulazione con e senza Airbag ---")
    
    # Crea i due certificati
    cert_no_airbag = create_express_test_cert(airbag_enabled=False)
    cert_with_airbag = create_express_test_cert(airbag_enabled=True)
    
    # Esegui le simulazioni (con un seed per avere risultati confrontabili)
    print("\nSimulazione per certificato SENZA Airbag...")
    paths_no_airbag = cert_no_airbag.simulate_price_paths(n_simulations=20000, seed=42)
    results_no_airbag = cert_no_airbag.calculate_express_payoffs(paths_no_airbag)
    
    print("\nSimulazione per certificato CON Airbag...")
    paths_with_airbag = cert_with_airbag.simulate_price_paths(n_simulations=20000, seed=42)
    results_with_airbag = cert_with_airbag.calculate_express_payoffs(paths_with_airbag)
    
    # Stampa i risultati
    print("\n" + "="*50)
    print("RISULTATI COMPARATIVI")
    print("="*50)
    print(f"{'Metrica':<20} | {'SENZA Airbag':<15} | {'CON Airbag':<15}")
    print("-"*50)
    
    payoff_no_airbag = f"€{results_no_airbag['payoff_medio']:.2f}"
    payoff_with_airbag = f"€{results_with_airbag['payoff_medio']:.2f}"
    print(f"{'Payoff Medio':<20} | {payoff_no_airbag:<15} | {payoff_with_airbag:<15}")
    
    loss_prob_no = f"{results_no_airbag['prob_perdita']:.2%}"
    loss_prob_with = f"{results_with_airbag['prob_perdita']:.2%}"
    print(f"{'Prob. di Perdita':<20} | {loss_prob_no:<15} | {loss_prob_with:<15}")
    
    max_loss_no = f"{results_no_airbag['perdita_massima']:.2%}"
    max_loss_with = f"{results_with_airbag['perdita_massima']:.2%}"
    print(f"{'Perdita Massima':<20} | {max_loss_no:<15} | {max_loss_with:<15}")
    print("="*50)

    # Verifica
    if results_with_airbag['payoff_medio'] > results_no_airbag['payoff_medio']:
        print("\n✅ VERIFICA OK: Il payoff medio con Airbag è più alto.")
    else:
        print("\n❌ ERRORE: Il payoff medio con Airbag non è migliorato.")

if __name__ == "__main__":
    run_analysis()