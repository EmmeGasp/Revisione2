# analysis_airbag_simulation.py

import sys
import os
import numpy as np

# --- INIZIO CORREZIONE PERCORSO ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './src')))
# --- FINE CORREZIONE PERCORSO ---

from datetime import datetime
# Ora importiamo le classi per il PHOENIX
from app.core.unified_certificates import PhoenixCertificate, CouponSchedule
from app.core.structural_cleanup import CertificateSpecs

def create_phoenix_test_cert(airbag_enabled: bool) -> PhoenixCertificate:
    """Funzione helper per creare un certificato Phoenix di test."""
    
    protection = 60.0 if airbag_enabled else 0.0
    
    specs = CertificateSpecs(
        name=f"Phoenix Test (Airbag: {airbag_enabled})",
        isin="ISIN_TEST_PHOENIX",
        underlying="MULTI_ASSET",
        issue_date=datetime(2024, 1, 1),
        maturity_date=datetime(2027, 1, 1), # Durata 3 anni
        strike=100.0,
        protection_level=protection
    )
    
    # Schedule coupon annuale
    coupon_schedule = CouponSchedule(
        payment_dates=[datetime(2025, 1, 1), datetime(2026, 1, 1), datetime(2027, 1, 1)],
        rates=[0.08, 0.08, 0.08]
    )

    cert = PhoenixCertificate(
        specs=specs,
        underlying_assets=["ASSET_A", "ASSET_B"],
        initial_prices=[100.0, 100.0],
        coupon_schedule=coupon_schedule,
        barrier_coupon=0.70,
        barrier_capitale=0.60, # Barriera capitale al 60%
        memory_coupon=True,
        notional=1000.0,
        airbag_feature=airbag_enabled,
        airbag_level=0.60 if airbag_enabled else None
    )
    
    # Parametri di mercato
    correlations = np.array([[1.0, 0.5], [0.5, 1.0]])
    cert.setup_market_parameters(
        spot_prices=[100.0, 100.0],
        volatilities=[0.35, 0.35], # Volatilità alta per vedere l'effetto
        correlations=correlations,
        risk_free_rate=0.01,
        dividends=[0.0, 0.0]
    )
    return cert

def run_analysis():
    """Esegue l'analisi comparativa."""
    
    print("--- Avvio analisi PHOENIX con e senza Airbag ---")
    
    cert_no_airbag = create_phoenix_test_cert(airbag_enabled=False)
    cert_with_airbag = create_phoenix_test_cert(airbag_enabled=True)
    
    print("\nSimulazione per certificato SENZA Airbag...")
    paths = cert_no_airbag.simulate_price_paths(n_simulations=20000, seed=42)
    results_no_airbag = cert_no_airbag.calculate_phoenix_payoffs(paths)
    
    print("\nSimulazione per certificato CON Airbag...")
    # Usiamo gli stessi percorsi per un confronto diretto
    results_with_airbag = cert_with_airbag.calculate_phoenix_payoffs(paths)
    
    # Aggiungiamo la perdita massima per un confronto completo
    notional = cert_no_airbag.notional
    results_no_airbag['perdita_massima'] = np.min(results_no_airbag['payoffs']) / notional - 1
    results_with_airbag['perdita_massima'] = np.min(results_with_airbag['payoffs']) / notional - 1

    print("\n" + "="*50)
    print("RISULTATI COMPARATIVI PHOENIX")
    print("="*50)
    print(f"{'Metrica':<25} | {'SENZA Airbag':<15} | {'CON Airbag':<15}")
    print("-"*55)
    
    payoff_no_airbag = f"€{results_no_airbag['payoff_medio']:.2f}"
    payoff_with_airbag = f"€{results_with_airbag['payoff_medio']:.2f}"
    print(f"{'Payoff Medio':<25} | {payoff_no_airbag:<15} | {payoff_with_airbag:<15}")
    
    loss_prob_no = f"{results_no_airbag['prob_perdita_capitale']:.2%}"
    loss_prob_with = f"{results_with_airbag['prob_perdita_capitale']:.2%}"
    print(f"{'Prob. Perdita Capitale':<25} | {loss_prob_no:<15} | {loss_prob_with:<15}")
    
    max_loss_no = f"{results_no_airbag['perdita_massima']:.2%}"
    max_loss_with = f"{results_with_airbag['perdita_massima']:.2%}"
    print(f"{'Perdita Massima':<25} | {max_loss_no:<15} | {max_loss_with:<15}")
    print("="*55)

    if results_with_airbag['payoff_medio'] > results_no_airbag['payoff_medio']:
        print("\n✅ VERIFICA OK: Il payoff medio con Airbag è più alto.")
    else:
        print("\n❌ ERRORE: Il payoff medio con Airbag non è migliorato.")

if __name__ == "__main__":
    run_analysis()