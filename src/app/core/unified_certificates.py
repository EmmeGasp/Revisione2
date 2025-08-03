# ==========================================================
# RIEPILOGO CONTENUTO FILE:
# - (Da completare: elenco classi e funzioni una volta che il file sarà popolato)
# ==========================================================

# ========================================
# File: unifed_certificates.py 
# Sistema Certificati Finanziari - Certificati consolidati
# Timestamp: 2025-06-16 12:01:00
# Modifica del metodo ExpressCertificate.calculate_express_payoffs
# per implementare la logica dei prezzi che tenga conto
# di tutte le opzioni disponibili per questa tipologia di certificato
# ========================================

"""
ISTRUZIONI DI APPLICAZIONE:

1. Questo file VA AGGIUNTO dopo structural_cleanup.py
2. SOSTITUISCE tutte le implementazioni certificate frammentate
3. Unifica ExpressCertificate e EsempioCompletoExpress
4. Unifica PhoenixCertificate e EsempioCompletoPhoenix
5. Mantiene inheritance hierarchy corretta

COSA È STATO UNIFICATO:
✅ ExpressCertificate completa (da Parte 3 + Parte 5a)
✅ PhoenixCertificate completa (da Parte 5a)
✅ Tutti i certificati ereditano da CertificateBase
✅ Factory pattern unificato
✅ Analyzer unificato
"""
from typing import Union, List
# ========================================
# IMPORTS (dipende da structural_cleanup.py)
# ========================================

from .structural_cleanup import (
    CertificateBase, CertificateSpecs, MarketData, UnifiedValidator,
    MonteCarloEngine, BlackScholesModel, DateUtils,
    np, pd, datetime, timedelta, Dict, List, Optional, Union, Enum,
    logger, dataclass
)
import logging  # Fix: Import mancante per UnifiedCertificateAnalyzer
from scipy import stats  # Fix: Import mancante per calculate_risk_metrics

# ========================================
# ENUMS E DATACLASSES PER CERTIFICATI
# ========================================

class CertificateType(Enum):
    """Enumerazione dei tipi di certificati - CONSOLIDATA"""
    CAPITAL_PROTECTION = "capital_protection"
    BONUS = "bonus"
    DISCOUNT = "discount"
    OUTPERFORMANCE = "outperformance"
    REVERSE_CONVERTIBLE = "reverse_convertible"
    EXPRESS = "express"
    BARRIER_REVERSE_CONVERTIBLE = "barrier_reverse_convertible"
    TWIN_WIN = "twin_win"
    PHOENIX = "phoenix"
    AUTOCALLABLE = "autocallable"
    BARRIER = "barrier"

class BarrierType(Enum):
    """Tipi di barriera - CONSOLIDATA"""
    AMERICAN = "american"
    EUROPEAN = "european"
    DIGITAL = "digital"
    PARTIAL = "partial"

@dataclass
class Barrier:
    """Rappresenta una barriera del certificato - CONSOLIDATA"""
    level: float
    type: BarrierType
    observation_dates: Optional[List[datetime]] = None
    is_active: bool = True
    hit_date: Optional[datetime] = None
    
    def is_breached(self, spot_price: float, initial_price: float, 
                   current_date: datetime = None) -> bool:
        """Verifica se la barriera è stata violata"""
        barrier_level = initial_price * self.level
        
        if self.type == BarrierType.AMERICAN:
            return spot_price <= barrier_level
        elif self.type == BarrierType.EUROPEAN:
            if current_date and self.observation_dates:
                return (current_date in self.observation_dates and 
                       spot_price <= barrier_level)
        
        return False

@dataclass
class CouponSchedule:
    """Programma di pagamento delle cedole - CONSOLIDATA"""
    payment_dates: List[datetime]
    rates: List[float]
    conditions: List[str] = None
    memory_feature: bool = False
    
    def get_coupon_rate(self, date: datetime) -> float:
        """Ottiene il tasso di cedola per una data specifica"""
        for i, payment_date in enumerate(self.payment_dates):
            if date <= payment_date:
                return self.rates[i] if i < len(self.rates) else 0.0
        return 0.0

# ========================================
# EXPRESS CERTIFICATE UNIFICATA
# ========================================

class ExpressCertificate(CertificateBase):
   
    def __init__(self, specs: CertificateSpecs, underlying_assets: List[str],
                 initial_prices: List[float],
                 coupon_schedule: CouponSchedule, autocall_levels: List[float],
                 autocall_dates: List[datetime], barrier: Barrier,
                 memory_coupon: bool = True, notional: float = 100.0,
                 airbag_feature: bool = False, 
                 airbag_level: Optional[float] = None,
                 dynamic_barrier_feature: bool = False,
                 dynamic_barrier_start_level: Optional[float] = None,
                 step_down_rate: Optional[float] = None,
                 dynamic_barrier_end_level: Optional[float] = None,
                 observation_delay_months: Optional[int] = None
                ):
        
        
        # Aggiorna specs per Express
        specs.certificate_type = CertificateType.EXPRESS.value
        super().__init__(specs)
        
        self.underlying_assets = underlying_assets
        self.initial_prices = initial_prices
        self.coupon_schedule = coupon_schedule
        self.autocall_levels = autocall_levels
        self.autocall_dates = autocall_dates
        self.barrier = barrier
        self.memory_coupon = memory_coupon
        self.notional = notional
        self.airbag_feature = airbag_feature
        self.airbag_level = airbag_level
        self.capital_barrier = barrier.level # Aggiungiamo questo per coerenza con il risk analyzer
        self.dynamic_barrier_feature = dynamic_barrier_feature
        self.dynamic_barrier_start_level = dynamic_barrier_start_level
        self.step_down_rate = step_down_rate
        self.dynamic_barrier_end_level = dynamic_barrier_end_level
        self.observation_delay_months = observation_delay_months        
        # Parametri avanzati (da EsempioCompletoExpress)
        self.parametri_mercato = {}
        self.risultati_simulazione = {}
        
        # Validazione
        self._validate_express_parameters()
    
    def _validate_express_parameters(self):
        """Validazione parametri specifici Express"""
        if len(self.autocall_levels) != len(self.autocall_dates):
            raise ValueError("Autocall levels e dates devono avere stessa lunghezza")
        
        if len(self.coupon_schedule.payment_dates) != len(self.coupon_schedule.rates):
            raise ValueError("Payment dates e rates devono avere stessa lunghezza")
        
        for level in self.autocall_levels:
            if level <= 0:
                raise ValueError("Autocall levels devono essere positivi")
    
    def setup_market_parameters(self, spot_prices: List[float], volatilities: List[float],
                              correlations: np.ndarray, risk_free_rate: float,
                              dividends: List[float] = None):
        """Setup parametri di mercato avanzati (da EsempioCompletoExpress)"""
        
        if dividends is None:
            dividends = [0.0] * len(spot_prices)
        
        self.parametri_mercato = {
            'spot_prices': spot_prices,
            'volatilita': volatilities,
            'correlazioni': correlations,
            'tasso_libero_rischio': risk_free_rate,
            'dividendi': dividends,
            'data_valutazione': datetime.now()
        }
        
        # Crea MarketData per compatibility
        # Fix: Crea date multiple per match con prezzi multipli
        dates = [datetime.now() - timedelta(days=i) for i in range(len(spot_prices))]
        market_data = MarketData(
            dates=dates,                         # ✅ Stesso numero di elementi
            prices=spot_prices,                  # ✅ Stesso numero di elementi
            volatility=np.mean(volatilities),
            risk_free_rate=risk_free_rate,
            dividend_yield=np.mean(dividends)
        )
        #self.set_market_data(market_data)
        
        logger.info(f"Parametri mercato Express configurati: {len(spot_prices)} assets")
    
    def simulate_price_paths(self, n_simulations: int = 10000, n_steps: int = None, seed: int=None) -> np.ndarray:
        """Simula percorsi prezzo multi-asset (da EsempioCompletoExpress)"""
        
        if not self.parametri_mercato:
            raise ValueError("Parametri mercato non configurati. Usa setup_market_parameters()")

        if seed is not None:
            np.random.seed(seed)

        if n_steps is None:
            years_to_maturity = self.get_time_to_maturity()
            n_steps = int(years_to_maturity * 252)
        
        logger.info(f"Simulazione Express: {n_simulations:,} percorsi, {n_steps} steps")
        
        n_assets = len(self.parametri_mercato['spot_prices'])
        dt = 1/252
        
        # Parametri
        S0 = np.array(self.parametri_mercato['spot_prices'])
        vol = np.array(self.parametri_mercato['volatilita'])
        r = self.parametri_mercato['tasso_libero_rischio']
        div = np.array(self.parametri_mercato['dividendi'])
        corr = self.parametri_mercato['correlazioni']
        
        # Decomposizione Cholesky per correlazioni
        L = np.linalg.cholesky(corr)
        
        # Array percorsi
        percorsi = np.zeros((n_simulations, n_assets, n_steps + 1))
        percorsi[:, :, 0] = S0
        
        # Simulazione Monte Carlo multi-asset
        for t in range(1, n_steps + 1):
            Z = np.random.standard_normal((n_simulations, n_assets))
            
            # Applica correlazioni
            Z_corr = np.zeros_like(Z)
            for i in range(n_simulations):
                Z_corr[i] = Z[i] @ L.T
            
            # Aggiorna prezzi
            drift = (r - div - 0.5 * vol**2) * dt
            diffusion = vol * np.sqrt(dt) * Z_corr
            
            percorsi[:, :, t] = percorsi[:, :, t-1] * np.exp(drift + diffusion)
        
        self.risultati_simulazione['percorsi'] = percorsi
        logger.info("Simulazione Express completata")
        return percorsi
    
    def calculate_express_payoffs(self, percorsi: np.ndarray = None) -> Dict:
        """
        Calcola i payoff per un Express Certificate.
        *** VERSIONE CORRETTA: Utilizza la schedule dinamica anche per l'autocall. ***
        """
        from app.utils.date_utils import DateCalculationUtils  # Spostato import per evitare problemi
        from app.core.real_certificate_integration import UnderlyingEvaluationEngine

        dynamic_schedule = {}
        if hasattr(self, 'base_config') and getattr(self, 'dynamic_barrier_feature', False):
            dynamic_schedule = DateCalculationUtils.generate_dynamic_barrier_schedule(self.base_config)
            if dynamic_schedule:
                print("🧬 Logica Autocall utilizzerà la schedule della barriera dinamica.")

        evaluation_type = getattr(self, 'underlying_evaluation', 'worst_of')
        
        if percorsi is None:
            if 'percorsi' not in self.risultati_simulazione:
                raise ValueError("Nessun percorso disponibile. Esegui simulate_price_paths()")
            percorsi = self.risultati_simulazione['percorsi']
        
        logger.info("Calcolo payoff Express...")
        
        n_sim, n_assets, n_steps = percorsi.shape
        S0 = np.array(self.initial_prices)
        notional = self.notional

        payoffs = np.zeros(n_sim)
        tempi_uscita = np.full(n_sim, self.get_time_to_maturity())
        autocall_flags = np.zeros(n_sim, dtype=bool)
        coupon_pagati = np.zeros(n_sim)
        
        date_oss = []
        for date in self.autocall_dates:
            days_from_issue = (date - self.specs.issue_date).days
            step = int(days_from_issue * 252 / 365.25)
            date_oss.append(min(step, n_steps - 1))
        
        for sim in range(n_sim):
            performance = np.zeros(n_steps)
            for step in range(n_steps):
                current_prices = percorsi[sim, :, step]
                performance[step] = UnderlyingEvaluationEngine.calculate_performance(
                    current_prices, S0, evaluation_type
                )

            autocalled = False
            
            for i, step in enumerate(date_oss):
                if step < n_steps and not autocalled:
                    perf_at_date = performance[step]

                    # --- INIZIO LOGICA CORRETTA PER LIVELLO AUTOCALL ---
                    current_obs_date = self.autocall_dates[i]
                    current_obs_date_str = current_obs_date.strftime('%Y-%m-%d')
                    
                    # Di default, usa il livello di autocall fisso definito
                    autocall_level_da_usare = self.autocall_levels[i]
                    
                    # Se esiste una schedule dinamica E la data corrente è in essa,
                    # SOVRASCRIVI il livello di autocall con quello dinamico.
                    if dynamic_schedule and current_obs_date_str in dynamic_schedule:
                        autocall_level_da_usare = dynamic_schedule[current_obs_date_str]
                    # --- FINE LOGICA CORRETTA PER LIVELLO AUTOCALL ---

                    if perf_at_date >= autocall_level_da_usare:
                        anni_trascorsi = (self.autocall_dates[i] - self.specs.issue_date).days / 365.25
                        
                        if self.memory_coupon:
                            coupon_totale = sum(self.coupon_schedule.rates[:i+1])
                        else:
                            coupon_totale = self.coupon_schedule.rates[i]
                        
                        payoffs[sim] = notional * (1 + coupon_totale)
                        tempi_uscita[sim] = anni_trascorsi
                        autocall_flags[sim] = True
                        coupon_pagati[sim] = coupon_totale * notional
                        autocalled = True
                        break
            
            # ... il resto del metodo (logica a scadenza con airbag etc.) rimane invariato ...
            if not autocalled:
                final_prices = percorsi[sim, :, -1]
                barrier_breached = UnderlyingEvaluationEngine.check_barrier_breach(
                    final_prices, S0, self.barrier.level, evaluation_type
                )

                if not barrier_breached:                
                    coupon_totale = sum(self.coupon_schedule.rates)
                    payoffs[sim] = notional * (1 + coupon_totale)
                    coupon_pagati[sim] = coupon_totale * notional
                else:
                    reference_prices = S0
                    if self.airbag_feature:
                        barrier_price_level = self.barrier.level
                        reference_prices = S0 * barrier_price_level
                        
                    final_performance = UnderlyingEvaluationEngine.calculate_performance(
                        final_prices, reference_prices, evaluation_type
                    )
                    
                    payoffs[sim] = notional * max(0, final_performance)
                    coupon_pagati[sim] = 0
        
        # ... il resto del metodo (creazione dizionario risultati) rimane invariato ...
        risultati = {
            'payoffs': payoffs,
            'tempi_uscita': tempi_uscita,
            'autocall_flags': autocall_flags,
            'coupon_pagati': coupon_pagati,
            'prob_autocall': np.mean(autocall_flags),
            'tempo_medio_uscita': np.mean(tempi_uscita),
            'payoff_medio': np.mean(payoffs),
            'perdita_massima': (np.min(payoffs) / notional - 1) if notional > 0 else 0,
            'prob_perdita': np.mean(payoffs < notional)
        }
        
        self.risultati_simulazione['payoffs'] = risultati
        logger.info(f"Payoff Express calcolati - Prob autocall: {risultati['prob_autocall']:.2%}")
        return risultati

    def calculate_payoff(self, spot_prices: Union[float, List[float]]) -> float:
        """
        Calcola il payoff del certificato. Questa versione è pienamente compatibile
        con la classe base e gestisce sia un prezzo singolo che una lista.
        """
        # Se riceviamo una lista, usiamo solo il primo valore per questo calcolo specifico
        if isinstance(spot_prices, list):
            final_price = spot_prices[0]
        else:
            final_price = spot_prices

        # Assicuriamoci che face_value sia definito, con un default di 1000
        face_value = getattr(self.specs, 'face_value', 1000.0)

        # 1. Scenario sopra la barriera: rimborso del capitale
        if final_price >= self.barrier.level:
            return face_value

        # 2. Scenario sotto la barriera: logica di perdita
        elif final_price < self.barrier.level:
            # Di default, il riferimento è lo strike
            reference_price = self.specs.strike

            # CONDIZIONE AIRBAG: se c'è protezione, il riferimento diventa la barriera
            if self.specs.protection_level and self.specs.protection_level > 0:
                reference_price = self.barrier.level

            # Calcoliamo la performance rispetto al riferimento corretto
            performance = final_price / reference_price
            
            return face_value * performance
        
        return 0.0
    def get_greeks(self) -> Dict[str, float]:
        """Calcola greche per Express (semplificato)"""
        return {
            'delta': 0.7,  # Alta esposizione al sottostante
            'gamma': 0.05,
            'theta': -0.02,  # Decay temporale
            'vega': 0.25,   # Sensibile a volatilità
            'rho': 0.1
        }
    
    def analyze_sensitivity(self, param_ranges: Dict) -> Dict:
        """Analisi di sensitività (da EsempioCompletoExpress)"""
        if not self.parametri_mercato:
            raise ValueError("Parametri mercato non configurati")
        
        logger.info("Avvio analisi sensitività Express...")
        
        base_payoffs = self.calculate_express_payoffs()
        base_fair_value = np.mean(base_payoffs['payoffs'])
        
        sensitivity_results = {}
        
        # Sensitività volatilità
        if 'volatility_range' in param_ranges:
            vol_results = []
            original_vol = self.parametri_mercato['volatilita'].copy()
            
            for vol_mult in param_ranges['volatility_range']:
                self.parametri_mercato['volatilita'] = [v * vol_mult for v in original_vol]
                
                # Nuova simulazione
                percorsi = self.simulate_price_paths(n_simulations=3000)
                payoffs = self.calculate_express_payoffs(percorsi)
                fair_value = np.mean(payoffs['payoffs'])
                
                vol_results.append({
                    'multiplier': vol_mult,
                    'fair_value': fair_value,
                    'change_pct': (fair_value / base_fair_value - 1) * 100
                })
            
            # Ripristina volatilità
            self.parametri_mercato['volatilita'] = original_vol
            sensitivity_results['volatility'] = vol_results
        
        # Sensitività barriera
        if 'barrier_range' in param_ranges:
            barrier_results = []
            original_barrier = self.barrier.level
            
            for barrier_level in param_ranges['barrier_range']:
                self.barrier.level = barrier_level
                
                percorsi = self.simulate_price_paths(n_simulations=3000)
                payoffs = self.calculate_express_payoffs(percorsi)
                fair_value = np.mean(payoffs['payoffs'])
                
                barrier_results.append({
                    'barrier_level': barrier_level,
                    'fair_value': fair_value,
                    'change_pct': (fair_value / base_fair_value - 1) * 100
                })
            
            # Ripristina barriera
            self.barrier.level = original_barrier
            sensitivity_results['barrier'] = barrier_results
        
        logger.info("Analisi sensitività Express completata")
        return sensitivity_results

# ========================================
# PHOENIX CERTIFICATE UNIFICATA
# ========================================

class PhoenixCertificate(CertificateBase):

    
    def __init__(self, specs: CertificateSpecs, underlying_assets: List[str],
                 initial_prices: List[float],
                 coupon_schedule: CouponSchedule, barrier_coupon: float,
                 barrier_capitale: float, memory_coupon: bool = True,
                 notional: float = 100.0,
                 airbag_feature: bool = False, 
                 airbag_level: Optional[float] = None,
                 dynamic_barrier_feature: bool = False,
                 dynamic_barrier_start_level: Optional[float] = None,
                 step_down_rate: Optional[float] = None,
                 dynamic_barrier_end_level: Optional[float] = None,
                 observation_delay_months: Optional[int] = None
                ):
        
        # Aggiorna specs per Phoenix
        specs.certificate_type = CertificateType.PHOENIX.value
        super().__init__(specs)
        
        self.underlying_assets = underlying_assets
        self.coupon_schedule = coupon_schedule
        self.initial_prices = initial_prices
        self.barrier_coupon = barrier_coupon
        self.barrier_capitale = barrier_capitale
        self.memory_coupon = memory_coupon
        self.notional = notional
        self.airbag_feature = airbag_feature
        self.airbag_level = airbag_level
        self.capital_barrier = barrier_capitale # Aggiungiamo questo per coerenza con il risk analyzer
    
        self.dynamic_barrier_feature = dynamic_barrier_feature
        self.dynamic_barrier_start_level = dynamic_barrier_start_level
        self.step_down_rate = step_down_rate
        self.dynamic_barrier_end_level = dynamic_barrier_end_level
        self.observation_delay_months = observation_delay_months
        
        # Parametri avanzati
        self.parametri_mercato = {}
        self.risultati_simulazione = {}
        
        # Validazione
        self._validate_phoenix_parameters()
    
    def _validate_phoenix_parameters(self):
        """Validazione parametri specifici Phoenix"""
        if self.barrier_coupon <= 0 or self.barrier_coupon > 1:
            raise ValueError("Barrier coupon deve essere tra 0 e 1")
        
        if self.barrier_capitale <= 0 or self.barrier_capitale > 1:
            raise ValueError("Barrier capitale deve essere tra 0 e 1")
        
        if len(self.coupon_schedule.payment_dates) != len(self.coupon_schedule.rates):
            raise ValueError("Payment dates e rates devono avere stessa lunghezza")
    
    def setup_market_parameters(self, spot_prices: List[float], volatilities: List[float],
                              correlations: np.ndarray, risk_free_rate: float,
                              dividends: List[float] = None):
        """Setup parametri di mercato per Phoenix"""
        
        if dividends is None:
            dividends = [0.0] * len(spot_prices)
        
        self.parametri_mercato = {
            'spot_prices': spot_prices,
            'volatilita': volatilities,
            'correlazioni': correlations,
            'tasso_libero_rischio': risk_free_rate,
            'dividendi': dividends,
            'data_valutazione': datetime.now()
        }
        
        # Crea MarketData per compatibility
        # Fix: Crea date multiple per match con prezzi multipli
        dates = [datetime.now() - timedelta(days=i) for i in range(len(spot_prices))]
        market_data = MarketData(
            dates=dates,                         # ✅ Stesso numero di elementi
            prices=spot_prices,                  # ✅ Stesso numero di elementi
            volatility=np.mean(volatilities),
            risk_free_rate=risk_free_rate,
            dividend_yield=np.mean(dividends)
        )
        #self.set_market_data(market_data)
        
        logger.info(f"Parametri mercato Phoenix configurati: {len(spot_prices)} assets")
    
    def simulate_price_paths(self, n_simulations: int = 10000, seed: int = None) -> np.ndarray:
        """Simula percorsi prezzo Phoenix (osservazioni annuali)"""
        
        if not self.parametri_mercato:
            raise ValueError("Parametri mercato non configurati")

        if seed is not None:
            np.random.seed(seed)

        n_assets = len(self.parametri_mercato['spot_prices'])
        n_years = len(self.coupon_schedule.payment_dates)
        dt = 1.0  # Step annuali
        
        logger.info(f"Simulazione Phoenix: {n_simulations:,} percorsi, {n_years} anni")
        
        # Parametri
        S0 = np.array(self.parametri_mercato['spot_prices'])
        vol = np.array(self.parametri_mercato['volatilita'])
        r = self.parametri_mercato['tasso_libero_rischio']
        div = np.array(self.parametri_mercato['dividendi'])
        corr = self.parametri_mercato['correlazioni']
        
        # Decomposizione Cholesky
        L = np.linalg.cholesky(corr)
        
        # Array percorsi
        percorsi = np.zeros((n_simulations, n_assets, n_years + 1))
        percorsi[:, :, 0] = S0
        
        # Simulazione con step annuali
        for t in range(1, n_years + 1):
            Z = np.random.standard_normal((n_simulations, n_assets))
            
            Z_corr = np.zeros_like(Z)
            for i in range(n_simulations):
                Z_corr[i] = Z[i] @ L.T
            
            drift = (r - div - 0.5 * vol**2) * dt
            diffusion = vol * np.sqrt(dt) * Z_corr
            
            percorsi[:, :, t] = percorsi[:, :, t-1] * np.exp(drift + diffusion)
        
        self.risultati_simulazione['percorsi'] = percorsi
        logger.info("Simulazione Phoenix completata")
        return percorsi
    

    def calculate_phoenix_payoffs(self, percorsi: np.ndarray = None) -> Dict:
        from app.core.enhanced_certificate_manager_fixed import DateCalculationUtils
        from app.core.real_certificate_integration import UnderlyingEvaluationEngine
        
        dynamic_schedule = {}
        if hasattr(self, 'base_config'):
            dynamic_schedule = DateCalculationUtils.generate_dynamic_barrier_schedule(self.base_config)
            # Aggiungiamo un log per chiarezza
            if dynamic_schedule:
                print("🧬 Logica Phoenix utilizzerà la schedule della barriera dinamica.")

        evaluation_type = getattr(self, 'underlying_evaluation', 'worst_of')
        if hasattr(self, 'parametri_mercato') and 'underlying_evaluation' in self.parametri_mercato:
            evaluation_type = self.parametri_mercato['underlying_evaluation']
        elif hasattr(self, 'config_data') and 'underlying_evaluation' in self.config_data:
            evaluation_type = self.config_data['underlying_evaluation']
        
        if percorsi is None:
            if 'percorsi' not in self.risultati_simulazione:
                raise ValueError("Nessun percorso disponibile")
            percorsi = self.risultati_simulazione['percorsi']
        
        logger.info("Calcolo payoff Phoenix...")
        
        n_sim, n_assets, n_steps = percorsi.shape
        S0 = np.array(self.initial_prices)
        notional = self.notional
        
        payoffs = np.zeros(n_sim)
        coupon_totali = np.zeros(n_sim)
        memoria_coupon = np.zeros(n_sim)
        
        for sim in range(n_sim):
            performance = np.zeros(n_steps)
            for step in range(n_steps):
                current_prices = percorsi[sim, :, step]
                performance[step] = UnderlyingEvaluationEngine.calculate_performance(
                    current_prices, S0, evaluation_type
                )

            coupon_sim = 0
            memoria_sim = 0
            
            # --- INIZIO LOGICA CEDOLE CON BARRIERA DINAMICA (MODIFICATA) ---
            for i, rate in enumerate(self.coupon_schedule.rates):
                if i + 1 < n_steps:
                    current_prices = percorsi[sim, :, i + 1]
                    
                    # Recupera la data di osservazione per la cedola
                    current_obs_date = self.coupon_schedule.payment_dates[i]
                    current_obs_date_str = current_obs_date.strftime('%Y-%m-%d')
                    
                    # <<< MODIFICA >>>: Determina la barriera cedola efficace: dinamica se disponibile, altrimenti fissa
                    effective_coupon_barrier = self.barrier_coupon
                    if dynamic_schedule and current_obs_date_str in dynamic_schedule:
                        effective_coupon_barrier = dynamic_schedule[current_obs_date_str]

                    coupon_barrier_met = not UnderlyingEvaluationEngine.check_barrier_breach(
                        current_prices, S0, effective_coupon_barrier, evaluation_type
                    )
                    
                    if coupon_barrier_met:                   
                        coupon_corrente = rate * notional
                        coupon_da_pagare = coupon_corrente + memoria_sim
                        coupon_sim += coupon_da_pagare
                        memoria_sim = 0
                    else:
                        if self.memory_coupon:
                            memoria_sim += rate * notional
            # --- FINE LOGICA CEDOLE ---
            
            final_prices = percorsi[sim, :, -1]

            # --- INIZIO LOGICA CAPITALE CON BARRIERA DINAMICA (MODIFICATA) ---
            # <<< MODIFICA >>>: Determina la barriera capitale efficace a scadenza
            effective_capital_barrier = self.barrier_capitale
            if dynamic_schedule:
                try:
                    # Usa l'ultimo valore della schedule dinamica come barriera capitale finale
                    effective_capital_barrier = list(dynamic_schedule.values())[-1]
                except IndexError:
                    # Fallback se la schedule fosse vuota per qualche motivo
                    pass

            capital_barrier_met = not UnderlyingEvaluationEngine.check_barrier_breach(
                final_prices, S0, effective_capital_barrier, evaluation_type
            )
            
            if capital_barrier_met:
                payoffs[sim] = notional + coupon_sim
            else:
                # La logica dell'Airbag ora utilizza la barriera capitale *efficace*
                reference_prices = S0
                if self.airbag_feature:
                    barrier_price_level = effective_capital_barrier
                    reference_prices = S0 * barrier_price_level
                
                final_performance = UnderlyingEvaluationEngine.calculate_performance(
                    final_prices, reference_prices, evaluation_type
                )
                
                capitale_finale = notional * max(0, final_performance)
                payoffs[sim] = capitale_finale + coupon_sim
            # --- FINE LOGICA CAPITALE ---

            coupon_totali[sim] = coupon_sim
            memoria_coupon[sim] = memoria_sim
        
        risultati = {
            'payoffs': payoffs,
            'coupon_totali': coupon_totali,
            'memoria_coupon_finale': memoria_coupon,
            'payoff_medio': np.mean(payoffs),
            'coupon_medio': np.mean(coupon_totali),
            'prob_perdita_capitale': np.mean(payoffs < notional),
            'prob_coupon_pagato': np.mean(coupon_totali > 0),
            'rendimento_totale_medio': np.mean(payoffs) / notional - 1,
            'efficacia_memoria': np.mean(coupon_totali) / (sum(self.coupon_schedule.rates) * notional if sum(self.coupon_schedule.rates) > 0 else 1)
        }
        
        self.risultati_simulazione['payoffs'] = risultati
        logger.info(f"Payoff Phoenix calcolati - Efficacia memoria: {risultati['efficacia_memoria']:.2%}")
        return risultati 

    def calculate_payoff(self, spot_prices: Union[float, List[float]]) -> Union[float, List[float]]:
        """
        Calcola il payoff del certificato a scadenza, gestendo correttamente la logica Airbag.
        Questa implementazione è per una valutazione statica (non include i coupon intermedi).
        """
        # Gestisce sia un prezzo singolo che una lista per coerenza
        if isinstance(spot_prices, (int, float)):
            spot_prices_list = [spot_prices]
        else:
            spot_prices_list = spot_prices

        payoffs = []
        
        # Assicuriamoci di usare il notional value definito nell'istanza
        notional = self.notional
        # Lo strike price è definito nelle specifiche
        strike_price = self.specs.strike
        # Il livello barriera per il capitale è un attributo della classe Phoenix
        capital_barrier_level_ratio = self.barrier_capitale
        
        # Calcoliamo il valore assoluto della barriera capitale
        capital_barrier_price = strike_price * capital_barrier_level_ratio

        for final_price in spot_prices_list:
            # 1. Scenario sopra o alla pari della barriera capitale: rimborso del capitale
            if final_price >= capital_barrier_price:
                payoffs.append(notional)
                continue

            # 2. Scenario sotto la barriera capitale: la perdita dipende dalla presenza dell'Airbag
            else:
                # Di default, il prezzo di riferimento per calcolare la perdita è lo strike
                reference_price = strike_price
                
                # CONDIZIONE AIRBAG:
                # Se l'airbag è attivo (tramite il suo attributo o protection_level),
                # il riferimento per il calcolo della perdita diventa il livello della barriera.
                if self.airbag_feature or (hasattr(self.specs, 'protection_level') and self.specs.protection_level > 0):
                    print("--- Airbag ATTIVO: il riferimento per il calcolo della perdita è la barriera ---")
                    reference_price = capital_barrier_price
                else:
                    print("--- Airbag NON attivo: il riferimento per il calcolo della perdita è lo strike ---")

                # Calcoliamo la performance rispetto al riferimento corretto (strike o barriera)
                performance = final_price / reference_price
                
                # Il payoff è proporzionale a questa performance
                payoffs.append(notional * max(0, performance))

        # Restituisce un singolo valore se l'input era singolo, altrimenti la lista
        return payoffs[0] if isinstance(spot_prices, (int, float)) else payoffs    

    def get_greeks(self) -> Dict[str, float]:
        """Calcola greche per Phoenix"""
        return {
            'delta': 0.6,
            'gamma': 0.08,
            'theta': -0.015,
            'vega': 0.3,
            'rho': 0.08
        }
    
    def analyze_memory_mechanism(self) -> Dict:
        """Analisi dettagliata meccanismo memoria"""
        if 'payoffs' not in self.risultati_simulazione:
            raise ValueError("Esegui prima calculate_phoenix_payoffs()")
        
        logger.info("Analisi meccanismo memoria Phoenix...")
        
        risultati = self.risultati_simulazione['payoffs']
        coupon_totali = risultati['coupon_totali']
        coupon_teorico_max = sum(self.coupon_schedule.rates) * self.notional
        
        analisi = {
            'coupon_medio_realizzato': np.mean(coupon_totali),
            'coupon_teorico_massimo': coupon_teorico_max,
            'efficacia_memoria': np.mean(coupon_totali) / coupon_teorico_max,
            'prob_coupon_completo': np.mean(coupon_totali >= coupon_teorico_max * 0.9),
            'distribuzione_coupon': {
                'min': np.min(coupon_totali),
                'q25': np.percentile(coupon_totali, 25),
                'median': np.median(coupon_totali),
                'q75': np.percentile(coupon_totali, 75),
                'max': np.max(coupon_totali)
            }
        }
        
        logger.info(f"Analisi memoria completata - Efficacia: {analisi['efficacia_memoria']:.2%}")
        return analisi

# ========================================
# FACTORY E ANALYZER UNIFICATI
# ========================================

class UnifiedCertificateFactory:
    """Factory unificata per creazione certificati - CONSOLIDATA"""
    
    @staticmethod
    def create_certificate(cert_type: CertificateType, **kwargs) -> CertificateBase:
        """Crea certificato del tipo specificato"""
        
        logger.info(f"Creazione certificato tipo: {cert_type.value}")
        
        if cert_type == CertificateType.EXPRESS:
            return UnifiedCertificateFactory._create_express(**kwargs)
        elif cert_type == CertificateType.PHOENIX:
            return UnifiedCertificateFactory._create_phoenix(**kwargs)
        elif cert_type == CertificateType.BARRIER:
            return UnifiedCertificateFactory._create_barrier(**kwargs)
        else:
            raise ValueError(f"Tipo certificato non supportato: {cert_type}")
    
    @staticmethod
    def _create_express(**kwargs) -> ExpressCertificate:
        """Crea certificato Express con parametri validati"""
        required_params = ['specs', 'underlying_assets', 'coupon_schedule', 
                          'autocall_levels', 'autocall_dates', 'barrier']
        
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Parametro obbligatorio mancante: {param}")
        
        return ExpressCertificate(**kwargs)
    
    @staticmethod
    def _create_phoenix(**kwargs) -> PhoenixCertificate:
        """Crea certificato Phoenix con parametri validati"""
        required_params = ['specs', 'underlying_assets', 'coupon_schedule',
                          'barrier_coupon', 'barrier_capitale']
        
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Parametro obbligatorio mancante: {param}")
        
        return PhoenixCertificate(**kwargs)
    
    @staticmethod
    def _create_barrier(**kwargs):
        """Crea certificato Barrier (dalla structural_cleanup)"""
        from app.core.structural_cleanup import BarrierCertificate
        return BarrierCertificate(**kwargs)

class UnifiedCertificateAnalyzer:
    """Analyzer unificato per tutti i tipi di certificati - CONSOLIDATO"""
    
    def __init__(self, certificate: CertificateBase):
        self.certificate = certificate
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_fair_value(self, n_simulations: int = 10000) -> Dict:
        """Calcola fair value unificato per qualsiasi tipo di certificato"""
        
        self.logger.info(f"Calcolo fair value per {type(self.certificate).__name__}")
        
        try:
            if isinstance(self.certificate, ExpressCertificate):
                return self._calculate_express_fair_value(n_simulations)
            elif isinstance(self.certificate, PhoenixCertificate):
                return self._calculate_phoenix_fair_value(n_simulations)
            else:
                # Pricing standard per altri tipi
                return self._calculate_standard_fair_value(n_simulations)
                
        except Exception as e:
            self.logger.error(f"Errore calcolo fair value: {e}")
            raise
    
    def _calculate_express_fair_value(self, n_simulations: int) -> Dict:
        """Fair value per Express Certificate"""
        
        if not self.certificate.parametri_mercato:
            raise ValueError("Parametri mercato Express non configurati")
        
        # Simula percorsi
        percorsi = self.certificate.simulate_price_paths(n_simulations)
        
        # Calcola payoff
        payoff_results = self.certificate.calculate_express_payoffs(percorsi)
        
        # Calcola valore presente
        r = self.certificate.parametri_mercato['tasso_libero_rischio']
        payoffs = payoff_results['payoffs']
        tempi_uscita = payoff_results['tempi_uscita']
        
        valore_presente = payoffs * np.exp(-r * tempi_uscita)
        fair_value = np.mean(valore_presente)
        
        std_err = np.std(valore_presente) / np.sqrt(len(valore_presente))
        ic_95 = [fair_value - 1.96 * std_err, fair_value + 1.96 * std_err]
        
        return {
            'fair_value': fair_value,
            'fair_value_percentage': fair_value / self.certificate.notional,
            'std_error': std_err,
            'confidence_interval_95': ic_95,
            'expected_return': (fair_value / self.certificate.notional - 1),
            'annualized_return': ((fair_value / self.certificate.notional) ** 
                               (1 / np.mean(tempi_uscita)) - 1),
            'autocall_probability': payoff_results['prob_autocall'],
            'average_exit_time': payoff_results['tempo_medio_uscita']
        }
    
    def _calculate_phoenix_fair_value(self, n_simulations: int) -> Dict:
        """Fair value per Phoenix Certificate"""
        
        if not self.certificate.parametri_mercato:
            raise ValueError("Parametri mercato Phoenix non configurati")
        
        # Simula percorsi
        percorsi = self.certificate.simulate_price_paths(n_simulations)
        
        # Calcola payoff
        payoff_results = self.certificate.calculate_phoenix_payoffs(percorsi)
        
        # Calcola valore presente (Phoenix ha scadenza fissa)
        r = self.certificate.parametri_mercato['tasso_libero_rischio']
        tempo_scadenza = len(self.certificate.coupon_schedule.payment_dates)
        
        payoffs = payoff_results['payoffs']
        valore_presente = payoffs * np.exp(-r * tempo_scadenza)
        fair_value = np.mean(valore_presente)
        
        std_err = np.std(valore_presente) / np.sqrt(len(valore_presente))
        ic_95 = [fair_value - 1.96 * std_err, fair_value + 1.96 * std_err]
        
        return {
            'fair_value': fair_value,
            'fair_value_percentage': fair_value / self.certificate.notional,
            'std_error': std_err,
            'confidence_interval_95': ic_95,
            'expected_return': (fair_value / self.certificate.notional - 1),
            'annualized_return': ((fair_value / self.certificate.notional) ** 
                               (1 / tempo_scadenza) - 1),
            'coupon_efficiency': payoff_results['efficacia_memoria'],
            'capital_loss_probability': payoff_results['prob_perdita_capitale']
        }
    
    def _calculate_standard_fair_value(self, n_simulations: int) -> Dict:
        """Fair value per certificati standard (Barrier, etc.)"""
        
        if not self.certificate.market_data:
            raise ValueError("Market data non disponibili")
        
        # Usa pricing standard da CertificateBase
        fair_value = self.certificate.calculate_price()
        
        return {
            'fair_value': fair_value,
            'fair_value_percentage': fair_value / self.certificate.specs.strike,
            'pricing_method': 'standard_monte_carlo'
        }
    
    def calculate_risk_metrics(self, n_simulations: int = 10000) -> Dict:
        """Calcola metriche di rischio unificate"""
        
        self.logger.info("Calcolo metriche di rischio")
        
        # Ottieni payoffs
        if isinstance(self.certificate, ExpressCertificate):
            if not self.certificate.risultati_simulazione.get('payoffs'):
                percorsi = self.certificate.simulate_price_paths(n_simulations)
                self.certificate.calculate_express_payoffs(percorsi)
            payoffs = self.certificate.risultati_simulazione['payoffs']['payoffs']
            
        elif isinstance(self.certificate, PhoenixCertificate):
            if not self.certificate.risultati_simulazione.get('payoffs'):
                percorsi = self.certificate.simulate_price_paths(n_simulations)
                self.certificate.calculate_phoenix_payoffs(percorsi)
            payoffs = self.certificate.risultati_simulazione['payoffs']['payoffs']
            
        else:
            # Simula payoffs per altri tipi
            payoffs = self._simulate_standard_payoffs(n_simulations)
        
        # Calcola rendimenti
        notional = getattr(self.certificate, 'notional', self.certificate.specs.strike)
        returns = (payoffs - notional) / notional
        
        # Metriche di rischio
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        cvar_95 = np.mean(returns[returns <= var_95])
        cvar_99 = np.mean(returns[returns <= var_99])
        
        volatility = np.std(returns)
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        # Sharpe ratio (assumendo risk-free rate)
        rf = getattr(self.certificate, 'risk_free_rate', 0.02)
        excess_return = np.mean(returns) - rf
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'volatility': volatility,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'sharpe_ratio': sharpe_ratio,
            'probability_loss': np.mean(returns < 0),
            'maximum_loss': np.min(returns),
            'maximum_gain': np.max(returns)
        }
    
    def _simulate_standard_payoffs(self, n_simulations: int) -> np.ndarray:
        """Simula payoffs per certificati standard"""
        
        if not self.certificate.market_data:
            raise ValueError("Market data necessari per simulazione")
        
        # Crea modello Black-Scholes
        model = BlackScholesModel(
            S0=self.certificate.get_current_spot(),
            r=self.certificate.risk_free_rate,
            T=self.certificate.get_time_to_maturity(),
            sigma=self.certificate.market_data.volatility or 0.2
        )
        
        # Simula percorsi
        mc_engine = MonteCarloEngine(model, n_simulations)
        paths = mc_engine.run_simulation()
        
        # Calcola payoffs
        final_prices = paths[:, -1]
        payoffs = np.array([self.certificate.calculate_payoff(price) for price in final_prices])
        
        return payoffs
    
    def compare_scenarios(self, scenarios: Dict[str, Dict]) -> Dict:
        """Confronta il certificato sotto diversi scenari"""
        
        self.logger.info(f"Confronto {len(scenarios)} scenari")
        
        results = {}
        
        for scenario_name, params in scenarios.items():
            try:
                # Salva parametri originali
                if isinstance(self.certificate, (ExpressCertificate, PhoenixCertificate)):
                    original_params = self.certificate.parametri_mercato.copy()
                
                # Applica scenario
                if hasattr(self.certificate, 'setup_market_parameters'):
                    self.certificate.setup_market_parameters(**params)
                
                # Calcola fair value
                fv_result = self.calculate_fair_value(n_simulations=5000)
                
                # Calcola rischio
                risk_result = self.calculate_risk_metrics(n_simulations=5000)
                
                results[scenario_name] = {
                    'fair_value': fv_result['fair_value'],
                    'expected_return': fv_result['expected_return'],
                    'var_95': risk_result['var_95'],
                    'probability_loss': risk_result['probability_loss']
                }
                
                # Ripristina parametri originali
                if isinstance(self.certificate, (ExpressCertificate, PhoenixCertificate)):
                    self.certificate.parametri_mercato = original_params
                    
            except Exception as e:
                self.logger.error(f"Errore scenario {scenario_name}: {e}")
                results[scenario_name] = {'error': str(e)}
        
        return results


    def analyze_parameter_sensitivity(self, parameter_name: str, value_range: List[float], n_simulations: int = 5000) -> Dict:
        """
        Analizza la sensitività del Fair Value con un numero di simulazioni personalizzato.
        """
        self.logger.info(f"Avvio analisi di sensitività per il parametro: {parameter_name}")
        
        if not isinstance(self.certificate, (ExpressCertificate, PhoenixCertificate)) or not self.certificate.parametri_mercato:
            raise ValueError("L'analisi di sensitività è supportata solo per certificati con parametri di mercato configurati.")
        
        original_params = self.certificate.parametri_mercato.copy()
        try:
            base_result = self.calculate_fair_value(n_simulations=n_simulations)
            base_fair_value = base_result['fair_value']
            self.logger.info(f"Fair Value di base per sensitività: €{base_fair_value:.2f}")
        except Exception as e:
            self.logger.error(f"Impossibile calcolare il Fair Value di base: {e}")
            self.certificate.parametri_mercato = original_params
            raise

        sensitivity_results = {'base_fair_value': base_fair_value, 'results': []}
        
        for value in value_range:
            try:
                temp_params = original_params.copy()
                if parameter_name == 'volatilita':
                    original_vols = np.array(original_params['volatilita'])
                    temp_params['volatilita'] = (original_vols * value).tolist()
                    self.certificate.parametri_mercato = temp_params
                    param_label = f"{value:.0%}"
                else:
                    self.logger.warning(f"Parametro '{parameter_name}' non supportato. Analisi interrotta.")
                    break

                self.logger.info(f"Test sensitività {parameter_name} con valore/moltiplicatore: {value}")
                
                if 'payoffs' in self.certificate.risultati_simulazione:
                    del self.certificate.risultati_simulazione['payoffs']
                
                fv_result = self.calculate_fair_value(n_simulations=n_simulations)
                fair_value = fv_result['fair_value']
                
                change_pct = (fair_value / base_fair_value - 1) if base_fair_value != 0 else 0

                sensitivity_results['results'].append({
                    'parameter_value': value,
                    'label': param_label,
                    'fair_value': fair_value,
                    'change_pct': change_pct
                })

            except Exception as e:
                self.logger.error(f"Errore durante l'analisi per {parameter_name}={value}: {e}")
                sensitivity_results['results'].append({
                    'parameter_value': value,
                    'error': str(e)
                })

        self.certificate.parametri_mercato = original_params
        self.logger.info("Analisi di sensitività completata. Parametri originali ripristinati.")
        
        return sensitivity_results

    def generate_performance_report(self) -> str:
        """Genera report di performance dettagliato"""
        
        try:
            # Calcola metriche
            fv_result = self.calculate_fair_value()
            risk_result = self.calculate_risk_metrics()
            
            # Genera report
            report = f"""
REPORT PERFORMANCE - {type(self.certificate).__name__}
{'=' * 60}

VALUTAZIONE:
  Fair Value: €{fv_result['fair_value']:.2f}
  Rendimento Atteso: {fv_result['expected_return']:.2%}
  Rendimento Annualizzato: {fv_result.get('annualized_return', 'N/A')}

METRICHE DI RISCHIO:
  VaR 95%: {risk_result['var_95']:.2%}
  VaR 99%: {risk_result['var_99']:.2%}
  CVaR 95%: {risk_result['cvar_95']:.2%}
  Volatilità: {risk_result['volatility']:.2%}
  Sharpe Ratio: {risk_result['sharpe_ratio']:.3f}

PROBABILITÀ:
  Perdita: {risk_result['probability_loss']:.2%}
  Perdita Massima: {risk_result['maximum_loss']:.2%}
  Guadagno Massimo: {risk_result['maximum_gain']:.2%}

CARATTERISTICHE DISTRIBUZIONE:
  Skewness: {risk_result['skewness']:.3f}
  Kurtosis: {risk_result['kurtosis']:.3f}
"""
            
            # Aggiungi metriche specifiche per tipo
            if isinstance(self.certificate, ExpressCertificate):
                report += f"""
METRICHE EXPRESS:
  Probabilità Autocall: {fv_result.get('autocall_probability', 'N/A'):.2%}
  Tempo Medio Uscita: {fv_result.get('average_exit_time', 'N/A'):.2f} anni
"""
            
            elif isinstance(self.certificate, PhoenixCertificate):
                report += f"""
METRICHE PHOENIX:
  Efficacia Memoria: {fv_result.get('coupon_efficiency', 'N/A'):.2%}
  Prob. Perdita Capitale: {fv_result.get('capital_loss_probability', 'N/A'):.2%}
"""
            
            report += "\n" + "=" * 60
            return report
            
        except Exception as e:
            self.logger.error(f"Errore generazione report: {e}")
            return f"ERRORE GENERAZIONE REPORT: {e}"

# ========================================
# FUNZIONI DI UTILITÀ E TESTING
# ========================================

def create_sample_express_certificate() -> ExpressCertificate:
    """Crea certificato Express di esempio per testing"""
    
    # Specifiche
    specs = CertificateSpecs(
        name="Express Certificate FTSE MIB",
        isin="XS1234567890",
        underlying="FTSE_MIB",
        issue_date=datetime(2024, 1, 15),
        maturity_date=datetime(2029, 1, 15),
        strike=100.0,
        certificate_type=CertificateType.EXPRESS.value
    )
    
    # Coupon schedule
    coupon_dates = [datetime(2025, 1, 15), datetime(2026, 1, 15), 
                   datetime(2027, 1, 15), datetime(2028, 1, 15), 
                   datetime(2029, 1, 15)]
    coupon_schedule = CouponSchedule(
        payment_dates=coupon_dates,
        rates=[0.08, 0.08, 0.08, 0.08, 0.08],  # 8% annuo
        memory_feature=True
    )
    
    # Barriera
    barrier = Barrier(level=0.65, type=BarrierType.EUROPEAN)
    
    # Autocall
    autocall_levels = [1.0, 1.0, 1.0, 1.0, 1.0]
    autocall_dates = coupon_dates
    
    # Crea certificato
    express_cert = ExpressCertificate(
        specs=specs,
        underlying_assets=["ENEL.MI", "ENI.MI", "INTESA.MI"],
        coupon_schedule=coupon_schedule,
        autocall_levels=autocall_levels,
        autocall_dates=autocall_dates,
        barrier=barrier,
        memory_coupon=True,
        notional=1000.0
    )
    
    # Setup parametri mercato
    correlations = np.array([
        [1.0, 0.65, 0.72],
        [0.65, 1.0, 0.58],
        [0.72, 0.58, 1.0]
    ])
    
    express_cert.setup_market_parameters(
        spot_prices=[10.50, 15.20, 2.85],
        volatilities=[0.25, 0.28, 0.32],
        correlations=correlations,
        risk_free_rate=0.035,
        dividends=[0.04, 0.05, 0.03]
    )
    
    return express_cert

def create_sample_phoenix_certificate() -> PhoenixCertificate:
    """Crea certificato Phoenix di esempio per testing"""
    
    # Specifiche
    specs = CertificateSpecs(
        name="Phoenix Certificate US Tech",
        isin="XS9876543210",
        underlying="US_TECH",
        issue_date=datetime(2024, 1, 15),
        maturity_date=datetime(2030, 1, 15),
        strike=100.0,
        certificate_type=CertificateType.PHOENIX.value
    )
    
    # Coupon schedule
    coupon_dates = [datetime(2025, 1, 15), datetime(2026, 1, 15), 
                   datetime(2027, 1, 15), datetime(2028, 1, 15), 
                   datetime(2029, 1, 15), datetime(2030, 1, 15)]
    coupon_schedule = CouponSchedule(
        payment_dates=coupon_dates,
        rates=[0.09, 0.09, 0.09, 0.09, 0.09, 0.09],  # 9% annuo
        memory_feature=True
    )
    
    # Crea certificato
    phoenix_cert = PhoenixCertificate(
        specs=specs,
        underlying_assets=["AAPL", "MSFT", "GOOGL"],
        coupon_schedule=coupon_schedule,
        barrier_coupon=0.70,
        barrier_capitale=0.60,
        memory_coupon=True,
        notional=1000.0
    )
    
    # Setup parametri mercato
    correlations = np.array([
        [1.0, 0.75, 0.68],
        [0.75, 1.0, 0.70],
        [0.68, 0.70, 1.0]
    ])
    
    phoenix_cert.setup_market_parameters(
        spot_prices=[150.0, 280.0, 120.0],
        volatilities=[0.30, 0.28, 0.32],
        correlations=correlations,
        risk_free_rate=0.045,
        dividends=[0.006, 0.008, 0.0]
    )
    
    return phoenix_cert

def test_unified_certificates():
    """Test completo sistema certificati unificato"""
    
    print("=" * 60)
    print("TEST SISTEMA CERTIFICATI UNIFICATO")
    print("=" * 60)
    
    errors = []
    
    try:
        # Test 1: Creazione Express
        print("1. Test Express Certificate...")
        express_cert = create_sample_express_certificate()
        print(f"   ✅ Express creato: {express_cert.specs.name}")
        
        # Test pricing Express
        analyzer_express = UnifiedCertificateAnalyzer(express_cert)
        fv_express = analyzer_express.calculate_fair_value(n_simulations=2000)
        print(f"   ✅ Fair Value Express: €{fv_express['fair_value']:.2f}")
        
        # Test 2: Creazione Phoenix
        print("2. Test Phoenix Certificate...")
        phoenix_cert = create_sample_phoenix_certificate()
        print(f"   ✅ Phoenix creato: {phoenix_cert.specs.name}")
        
        # Test pricing Phoenix
        analyzer_phoenix = UnifiedCertificateAnalyzer(phoenix_cert)
        fv_phoenix = analyzer_phoenix.calculate_fair_value(n_simulations=2000)
        print(f"   ✅ Fair Value Phoenix: €{fv_phoenix['fair_value']:.2f}")
        
        # Test 3: Factory
        print("3. Test Unified Factory...")
        
        # Parametri per factory
        specs_factory = CertificateSpecs(
            name="Factory Test",
            isin="TEST123",
            underlying="TEST",
            issue_date=datetime(2024, 1, 1),
            maturity_date=datetime(2025, 1, 1),
            strike=100.0
        )
        
        barrier_test = Barrier(level=0.8, type=BarrierType.AMERICAN)
        
        barrier_cert = UnifiedCertificateFactory.create_certificate(
            CertificateType.BARRIER,
            specs=specs_factory,
            barrier_level=0.8,
            coupon_rate=0.05
        )
        print(f"   ✅ Factory Barrier: {type(barrier_cert).__name__}")
        
        # Test 4: Risk metrics
        print("4. Test Risk Metrics...")
        risk_express = analyzer_express.calculate_risk_metrics(n_simulations=1000)
        risk_phoenix = analyzer_phoenix.calculate_risk_metrics(n_simulations=1000)
        
        print(f"   ✅ Express VaR 95%: {risk_express['var_95']:.2%}")
        print(f"   ✅ Phoenix VaR 95%: {risk_phoenix['var_95']:.2%}")
        
        # Test 5: Scenario analysis
        print("5. Test Scenario Analysis...")
        
        scenarios = {
            'bull_market': {
                'spot_prices': [12.0, 18.0, 3.2],
                'volatilities': [0.20, 0.23, 0.28],
                'correlations': express_cert.parametri_mercato['correlazioni'],
                'risk_free_rate': 0.04,
                'dividends': [0.05, 0.06, 0.04]
            },
            'bear_market': {
                'spot_prices': [9.0, 12.0, 2.3],
                'volatilities': [0.35, 0.40, 0.45],
                'correlazioni': express_cert.parametri_mercato['correlazioni'],
                'risk_free_rate': 0.02,
                'dividends': [0.02, 0.03, 0.01]
            }
        }
        
        scenario_results = analyzer_express.compare_scenarios(scenarios)
        print(f"   ✅ Scenari analizzati: {len(scenario_results)}")
        
        for scenario, result in scenario_results.items():
            if 'error' not in result:
                print(f"      {scenario}: FV €{result['fair_value']:.2f}, "
                      f"Return {result['expected_return']:.2%}")
        
        # Test 6: Performance reports
        print("6. Test Performance Reports...")
        
        report_express = analyzer_express.generate_performance_report()
        print("   ✅ Report Express generato")
        
        report_phoenix = analyzer_phoenix.generate_performance_report()
        print("   ✅ Report Phoenix generato")
        
    except Exception as e:
        print(f"   ❌ Errore durante test: {e}")
        errors.append(str(e))
        import traceback
        traceback.print_exc()
    
    # Riepilogo
    print("\n" + "=" * 60)
    print("RIEPILOGO TEST CERTIFICATE UNIFICATION")
    print("=" * 60)
    
    if not errors:
        print("🎉 TUTTI I TEST PASSATI - CERTIFICATE UNIFICATION COMPLETATO!")
        print("\n✅ Unificazioni completate:")
        print("   - ExpressCertificate (Parte 3 + Parte 5a)")
        print("   - PhoenixCertificate (da Parte 5a)")
        print("   - UnifiedCertificateFactory")
        print("   - UnifiedCertificateAnalyzer")
        print("   - Sistema pricing unificato")
        print("   - Risk metrics consolidati")
        
        print("\n🚀 PRONTO PER STEP 3: Risk System Consolidation")
        return True
    else:
        print(f"❌ {len(errors)} ERRORI TROVATI:")
        for error in errors:
            print(f"   - {error}")
        return False

# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == "__main__":
    print("CERTIFICATE UNIFICATION - Sistema Certificati Finanziari")
    print("Versione Unificata - Express e Phoenix Consolidati")
    print("=" * 60)
    
    success = test_unified_certificates()
    
    if success:
        print("\n" + "🎯 CERTIFICATE UNIFICATION COMPLETATO CON SUCCESSO!")
        print("\nCLASSI UNIFICATE DISPONIBILI:")
        print("✅ ExpressCertificate - Completa (ex Parte 3 + 5a)")
        print("✅ PhoenixCertificate - Completa (ex Parte 5a)")
        print("✅ UnifiedCertificateFactory - Factory pattern")
        print("✅ UnifiedCertificateAnalyzer - Analisi unificata")
        print("✅ Barrier, CouponSchedule - Utilities")
        
        print(f"\n📊 STATISTICHE:")
        print(f"   Classi unificate: 2 (Express, Phoenix)")
        print(f"   Factory methods: 3")
        print(f"   Analyzer methods: 8")
        print(f"   Test scenarios: 6")
        
        print(f"\n⏭️  PROSSIMO STEP: Risk System Consolidation")
        
    else:
        print("\n❌ ERRORI NEL CERTIFICATE UNIFICATION - VERIFICARE LOG")