# analysis_dynamic_barrier_simulation.py

import sys
import os
import numpy as np
from datetime import datetime

# Aggiungiamo la cartella 'src' al path di Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './src')))

from app.core.unified_certificates import PhoenixCertificate, CouponSchedule
from app.core.structural_cleanup import CertificateSpecs
from app.core.real_certificate_integration import RealCertificateConfig

def create_phoenix_for_analysis(dynamic_barrier: bool) -> PhoenixCertificate:
    """Helper per creare un certificato Phoenix per l'analisi."""
    
    name = "Phoenix Dynamic" if dynamic_barrier else "Phoenix Fixed"
    
    base_config_dict = {
        'isin': f"ISIN_{name.replace(' ', '_').upper()}", 'name': name,
        'certificate_type': 'phoenix', 'issuer': 'Test Bank',
        'underlying_assets': ["ASSET_A.MI", "ASSET_B.MI"],
        'issue_date': datetime(2024, 1, 1), 'maturity_date': datetime(2027, 1, 1),
        'coupon_dates': [datetime(2025, 1, 1), datetime(2026, 1, 1), datetime(2027, 1, 1)],
        'coupon_rates': [0.08, 0.08, 0.08], 'notional': 1000.0,
        'dynamic_barrier_feature': dynamic_barrier,
        'dynamic_barrier_start_level': 0.70, 'step_down_rate': 0.05,
        'dynamic_barrier_end_level': 0.60, 'observation_delay_months': 0,
    }
    base_config = RealCertificateConfig(**base_config_dict)
    
    cert = PhoenixCertificate(
        specs=CertificateSpecs(isin=base_config.isin, name=base_config.name, underlying=", ".join(base_config.underlying_assets),
                              issue_date=base_config.issue_date, maturity_date=base_config.maturity_date, strike=100.0),
        underlying_assets=base_config.underlying_assets, initial_prices=[100.0, 100.0],
        coupon_schedule=CouponSchedule(payment_dates=base_config.coupon_dates, rates=base_config.coupon_rates),
        barrier_coupon=0.70, barrier_capitale=0.70, # Le barriere fisse di partenza sono le stesse
        memory_coupon=True, notional=base_config.notional
    )
    
    cert.base_config = base_config
    cert.setup_market_parameters(
        spot_prices=[100.0, 100.0], volatilities=[0.30, 0.30],
        correlations=np.array([[1.0, 0.5], [0.5, 1.0]]),
        risk_free_rate=0.02, dividends=[0.0, 0.0]
    )
    return cert

def run_analysis():
    print("--- Analisi Comparativa: Barriera Fissa vs. Dinamica (Step-Down) ---")
    
    cert_fixed = create_phoenix_for_analysis(dynamic_barrier=False)
    cert_dynamic = create_phoenix_for_analysis(dynamic_barrier=True)
    
    print("\nSimulazione per certificato con BARRIERA FISSA...")
    paths = cert_fixed.simulate_price_paths(n_simulations=20000, seed=42)
    results_fixed = cert_fixed.calculate_phoenix_payoffs(paths)
    
    print("\nSimulazione per certificato con BARRIERA DINAMICA...")
    results_dynamic = cert_dynamic.calculate_phoenix_payoffs(paths)
    
    print("\n" + "="*60)
    print("RISULTATI COMPARATIVI")
    print("="*60)
    print(f"{'Metrica':<25} | {'Barriera Fissa':<20} | {'Barriera Dinamica':<20}")
    print("-"*65)
    
    payoff_fixed = f"€{results_fixed['payoff_medio']:.2f}"
    payoff_dynamic = f"€{results_dynamic['payoff_medio']:.2f}"
    print(f"{'Payoff Medio':<25} | {payoff_fixed:<20} | {payoff_dynamic:<20}")
    
    eff_mem_fixed = f"{results_fixed['efficacia_memoria']:.2%}"
    eff_mem_dynamic = f"{results_dynamic['efficacia_memoria']:.2%}"
    print(f"{'Efficacia Memoria (Coupon)':<25} | {eff_mem_fixed:<20} | {eff_mem_dynamic:<20}")
    
    loss_prob_fixed = f"{results_fixed['prob_perdita_capitale']:.2%}"
    loss_prob_dynamic = f"{results_dynamic['prob_perdita_capitale']:.2%}"
    print(f"{'Prob. Perdita Capitale':<25} | {loss_prob_fixed:<20} | {loss_prob_dynamic:<20}")
    print("="*65)

    if results_dynamic['payoff_medio'] > results_fixed['payoff_medio']:
        print("\n✅ VERIFICA OK: La barriera dinamica ha migliorato il payoff medio.")
    else:
        print("\n❌ ERRORE: La barriera dinamica non ha migliorato il payoff.")

if __name__ == "__main__":
    run_analysis()