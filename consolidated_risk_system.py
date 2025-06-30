# ==========================================================
# RIEPILOGO CONTENUTO FILE:
# - Classi principali: RiskMetrics, UnifiedRiskAnalyzer, UnifiedStressTestEngine, UnifiedComplianceChecker, UnifiedRiskDashboard
# - Funzioni: test_consolidated_risk_system
# ==========================================================
# ========================================
# RISK SYSTEM CONSOLIDATION - SISTEMA RISCHI UNIFICATO
# Sistema Certificati Finanziari - Risk Management Consolidato
# ========================================
# File consolidated_risk_system.py ver 14.11
# Timestamp: 2025-06-16 00:09:50
# modifica per gestire i prezzi a fronte di molteplici opzioni disponibili
"""
ISTRUZIONI DI APPLICAZIONE:

1. Questo file VA AGGIUNTO dopo unified_certificates.py
2. CONSOLIDA tutto il sistema di risk management
3. UNIFICA RiskAnalyzer + SecurityValidator + StressTestEngine
4. ELIMINA duplicazioni di logica risk tra moduli
5. INTEGRA compliance checking

COSA È STATO CONSOLIDATO:
✅ RiskAnalyzer completo (da Parte 4 + logiche sparse)
✅ SecurityValidator integrato (da Parte 5b)
✅ StressTestEngine unificato
✅ ComplianceChecker consolidato
✅ Sistema alerting integrato
✅ Risk dashboard unificato
"""

# ========================================
# IMPORTS (dipende da structural_cleanup.py e unified_certificates.py)
# ========================================

from structural_cleanup import (
    UnifiedValidator, MonteCarloEngine, BlackScholesModel,
    np, pd, datetime, timedelta, Dict, List, Optional, Union,
    logger, stats, norm
)

from unified_certificates import (
    CertificateBase, ExpressCertificate, PhoenixCertificate,
    UnifiedCertificateAnalyzer, CertificateType
)

import logging  # Fix: Import mancante per logging
from typing import Tuple  # Fix: Import mancante per Tuple
import re
import secrets
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import time

# ========================================
# RISK METRICS E DATA STRUCTURES
# ========================================

@dataclass
class RiskMetrics:
    """Struttura unificata per metriche di rischio - CONSOLIDATA"""
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    max_drawdown: float
    volatility: float
    skewness: float
    kurtosis: float
    sharpe_ratio: float
    sortino_ratio: float
    
    # Metriche aggiuntive
    correlation_risk: float = 0.0
    concentration_risk: float = 0.0
    liquidity_risk: float = 0.0
    credit_risk: float = 0.0
    
    def to_dict(self) -> Dict:
        """Converte in dizionario per serializzazione"""
        return {
            'var_95': self.var_95,
            'var_99': self.var_99,
            'cvar_95': self.cvar_95,
            'cvar_99': self.cvar_99,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'correlation_risk': self.correlation_risk,
            'concentration_risk': self.concentration_risk,
            'liquidity_risk': self.liquidity_risk,
            'credit_risk': self.credit_risk
        }

class RiskLevel(Enum):
    """Livelli di rischio standardizzati"""
    VERY_LOW = "very_low"
    LOW = "low" 
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Tipi di alert di rischio"""
    THRESHOLD_BREACH = "threshold_breach"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    LIQUIDITY_STRESS = "liquidity_stress"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ERROR = "system_error"

@dataclass
class RiskAlert:
    """Struttura per alert di rischio"""
    alert_type: AlertType
    severity: RiskLevel
    message: str
    certificate_id: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# ========================================
# UNIFIED RISK ANALYZER
# ========================================

class UnifiedRiskAnalyzer:
    """Risk Analyzer unificato - CONSOLIDA Parte 4 + logiche sparse"""
    
    def __init__(self):
        self.risk_free_rate = 0.02
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Thresholds di default
        self.risk_thresholds = {
            'var_95': -0.10,  # -10%
            'var_99': -0.20,  # -20%
            'volatility': 0.50,  # 50%
            'concentration': 0.25,  # 25%
            'correlation': 0.90  # 90%
        }
        
        # Cache per performance
        self._cache = {}
        self._cache_ttl = {}
        self._cache_duration = 300  # 5 minuti
        
        self.logger.info("UnifiedRiskAnalyzer inizializzato")
    
    def set_risk_thresholds(self, thresholds: Dict[str, float]):
        """Configura soglie di rischio personalizzate"""
        self.risk_thresholds.update(thresholds)
        self.logger.info(f"Soglie rischio aggiornate: {thresholds}")
    
    def _get_cache_key(self, *args) -> str:
        """Genera chiave cache"""
        return hashlib.md5(str(args).encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica validità cache"""
        if cache_key not in self._cache_ttl:
            return False
        return datetime.now() < self._cache_ttl[cache_key]
    
    def _set_cache(self, cache_key: str, value):
        """Imposta valore in cache"""
        self._cache[cache_key] = value
        self._cache_ttl[cache_key] = datetime.now() + timedelta(seconds=self._cache_duration)
    
    def calculate_var(self, returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """Calcola Value at Risk - METODO CONSOLIDATO"""
        if len(returns) == 0:
            return 0.0
        
        # VaR parametrico (assumendo normalità)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if confidence_level == 0.95:
            z_score = -1.645  # 95% confidence
        elif confidence_level == 0.99:
            z_score = -2.326  # 99% confidence
        else:
            z_score = norm.ppf(1 - confidence_level)
        
        var_parametric = mean_return + z_score * std_return
        
        # VaR storico
        var_historical = np.percentile(returns, (1 - confidence_level) * 100)
        
        # Usa il più conservativo
        return min(var_parametric, var_historical)
    
    def calculate_cvar(self, returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """Calcola Conditional Value at Risk (Expected Shortfall)"""
        if len(returns) == 0:
            return 0.0
        
        var = self.calculate_var(returns, confidence_level)
        return np.mean(returns[returns <= var])
    
    def calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calcola massimo drawdown"""
        if len(prices) == 0:
            return 0.0
        
        # Calcola running maximum
        peak = np.maximum.accumulate(prices)
        
        # Calcola drawdown percentuale
        drawdown = (prices - peak) / peak
        
        return np.min(drawdown)
    
    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = None) -> float:
        """Calcola Sharpe ratio"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        excess_returns = np.mean(returns) - risk_free_rate / 252
        return excess_returns / np.std(returns) * np.sqrt(252)
    
    def calculate_sortino_ratio(self, returns: np.ndarray, risk_free_rate: float = None) -> float:
        """Calcola Sortino ratio"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) == 0:
            return 0.0
        
        excess_returns = np.mean(returns) - risk_free_rate / 252
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return float('inf')
        
        return excess_returns / downside_deviation * np.sqrt(252)
    
    def calculate_correlation_risk(self, returns_matrix: np.ndarray) -> float:
        """Calcola rischio di correlazione"""
        if returns_matrix.shape[1] < 2:
            return 0.0
        
        correlation_matrix = np.corrcoef(returns_matrix.T)
        
        # Rimuovi diagonale (correlazioni = 1)
        upper_triangle = correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)]
        
        # Rischio correlazione = correlazione media
        return np.mean(np.abs(upper_triangle))
    
    def calculate_concentration_risk(self, weights: np.ndarray) -> float:
        """Calcola rischio di concentrazione (Herfindahl Index)"""
        if len(weights) == 0:
            return 0.0
        
        # Normalizza pesi
        weights_norm = weights / np.sum(weights)
        
        # Herfindahl-Hirschman Index
        hhi = np.sum(weights_norm ** 2)
        
        return hhi
    
    def analyze_certificate_risk(self, certificate: CertificateBase, 
                                n_simulations: int = 10000) -> RiskMetrics:
        """Analizza rischio di un certificato - METODO CONSOLIDATO"""
        
        cache_key = self._get_cache_key(
            type(certificate).__name__, 
            certificate.specs.isin,
            n_simulations
        )
        
        if self._is_cache_valid(cache_key):
            self.logger.info(f"Usando cache per analisi rischio {certificate.specs.isin}")
            return self._cache[cache_key]
        
        self.logger.info(f"Analisi rischio per {certificate.specs.name}")
        
        try:
            # Usa UnifiedCertificateAnalyzer per ottenere payoffs
            analyzer = UnifiedCertificateAnalyzer(certificate)
            
            # Ottieni fair value e risk metrics
            if hasattr(certificate, 'risultati_simulazione') and certificate.risultati_simulazione:
                # Usa risultati esistenti se disponibili
                if isinstance(certificate, (ExpressCertificate, PhoenixCertificate)):
                    payoffs = certificate.risultati_simulazione.get('payoffs', {}).get('payoffs', [])
                    if len(payoffs) == 0:
                        payoffs = self._simulate_certificate_payoffs(certificate, n_simulations)
                else:
                    payoffs = self._simulate_certificate_payoffs(certificate, n_simulations)
            else:
                payoffs = self._simulate_certificate_payoffs(certificate, n_simulations)
            
            # Calcola rendimenti
            notional = getattr(certificate, 'notional', certificate.specs.strike)
            returns = (payoffs - notional) / notional
            
            # Calcola tutte le metriche
            var_95 = self.calculate_var(returns, 0.95)
            var_99 = self.calculate_var(returns, 0.99)
            cvar_95 = self.calculate_cvar(returns, 0.95)
            cvar_99 = self.calculate_cvar(returns, 0.99)
            max_drawdown = self.calculate_max_drawdown(payoffs)
            volatility = np.std(returns)
            skewness = stats.skew(returns)
            kurtosis = stats.kurtosis(returns)
            sharpe_ratio = self.calculate_sharpe_ratio(returns)
            sortino_ratio = self.calculate_sortino_ratio(returns)
            
            # Metriche aggiuntive per certificati multi-asset
            correlation_risk = 0.0
            concentration_risk = 0.0
            
            if hasattr(certificate, 'underlying_assets') and len(certificate.underlying_assets) > 1:
                # Simula returns per ogni asset (semplificato)
                n_assets = len(certificate.underlying_assets)
                returns_matrix = np.random.multivariate_normal(
                    mean=np.zeros(n_assets),
                    cov=np.eye(n_assets) * volatility**2,
                    size=min(1000, len(returns))
                )
                
                correlation_risk = self.calculate_correlation_risk(returns_matrix)
                weights = np.ones(n_assets) / n_assets  # Equal weight assumption
                concentration_risk = self.calculate_concentration_risk(weights)
            
            # Liquidity risk (semplificato basato su tipo certificato)
            liquidity_risk = self._estimate_liquidity_risk(certificate)
            
            # Credit risk (basato su specs)
            credit_risk = self._estimate_credit_risk(certificate)
            
            risk_metrics = RiskMetrics(
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                cvar_99=cvar_99,
                max_drawdown=max_drawdown,
                volatility=volatility,
                skewness=skewness,
                kurtosis=kurtosis,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                correlation_risk=correlation_risk,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk,
                credit_risk=credit_risk
            )
            
            # Cache risultato
            self._set_cache(cache_key, risk_metrics)
            
            self.logger.info(f"Analisi rischio completata per {certificate.specs.isin}")
            return risk_metrics
            
        except Exception as e:
            self.logger.error(f"Errore analisi rischio {certificate.specs.isin}: {e}")
            raise
    
    def _simulate_certificate_payoffs(self, certificate: CertificateBase, 
                                    n_simulations: int) -> np.ndarray:
        """Simula payoffs per il certificato"""
        
        if not certificate.market_data:
            raise ValueError("Market data necessari per simulazione")
        
        # Crea modello Monte Carlo
        model = BlackScholesModel(
            S0=certificate.get_current_spot(),
            r=certificate.risk_free_rate,
            T=certificate.get_time_to_maturity(),
            sigma=certificate.market_data.volatility or 0.2
        )
        
        mc_engine = MonteCarloEngine(model, n_simulations)
        paths = mc_engine.run_simulation()
        
        # *** AGGIORNATO v14.11 *** - Calcola payoffs con debug evaluation type
        final_prices = paths[:, -1]
       # Debug evaluation type se disponibile
        if hasattr(certificate, 'underlying_evaluation'):
            evaluation_type = certificate.underlying_evaluation
            print(f"🎯 Risk analysis con underlying evaluation: {evaluation_type}")
        elif hasattr(certificate, 'config_data') and 'underlying_evaluation' in certificate.config_data:
            evaluation_type = certificate.config_data['underlying_evaluation']
            print(f"🎯 Risk analysis con underlying evaluation (da config): {evaluation_type}")
        else:
            print(f"🎯 Risk analysis senza underlying evaluation (default worst_of)")
        
        payoffs = np.array([certificate.calculate_payoff(price) for price in final_prices])
        
        return payoffs
    
    def _estimate_liquidity_risk(self, certificate: CertificateBase) -> float:
        """Stima rischio di liquidità basato su caratteristiche certificato"""
        
        # Fattori di rischio liquidità
        time_to_maturity = certificate.get_time_to_maturity()
        
        # Più lungo = meno liquido
        maturity_factor = min(time_to_maturity / 10, 1.0)  # Max 10 anni
        
        # Tipo certificato
        cert_type = certificate.specs.certificate_type
        complexity_factors = {
            'bond': 0.1,
            'deposit': 0.05,
            'express': 0.3,
            'phoenix': 0.35,
            'barrier': 0.4,
            'autocallable': 0.3
        }
        
        complexity_factor = complexity_factors.get(cert_type, 0.25)
        
        return (maturity_factor + complexity_factor) / 2
    
    def _estimate_credit_risk(self, certificate: CertificateBase) -> float:
        """Stima rischio di credito"""
        
        # Basato su rating implicito (semplificato)
        # In implementazione reale, userebbe rating effettivi
        
        if hasattr(certificate, 'specs') and hasattr(certificate.specs, 'strike'):
            # Usa strike come proxy per qualità creditizia
            if certificate.specs.strike >= 100:
                return 0.1  # High grade
            elif certificate.specs.strike >= 75:
                return 0.2  # Investment grade
            else:
                return 0.4  # Below investment grade
        
        return 0.25  # Default
    
    def analyze_portfolio_risk(self, certificates: List[CertificateBase],
                             weights: Optional[List[float]] = None) -> Dict:
        """Analizza rischio di un portfolio di certificati"""
        
        if weights is None:
            weights = [1.0 / len(certificates)] * len(certificates)
        
        if len(weights) != len(certificates):
            raise ValueError("Lunghezza weights deve corrispondere a certificati")
        
        self.logger.info(f"Analisi portfolio risk per {len(certificates)} certificati")
        
        # Analizza ogni certificato
        individual_risks = []
        all_returns = []
        
        for cert in certificates:
            risk_metrics = self.analyze_certificate_risk(cert)
            individual_risks.append(risk_metrics)
            
            # Simula returns per correlazioni
            returns = np.random.normal(0, risk_metrics.volatility, 1000)
            all_returns.append(returns)
        
        # Calcola metriche portfolio aggregate
        all_returns = np.array(all_returns)
        weights = np.array(weights)
        
        # Portfolio returns (weighted)
        portfolio_returns = np.sum(all_returns * weights[:, np.newaxis], axis=0)
        
        # Metriche portfolio
        portfolio_var_95 = self.calculate_var(portfolio_returns, 0.95)
        portfolio_var_99 = self.calculate_var(portfolio_returns, 0.99)
        portfolio_volatility = np.std(portfolio_returns)
        portfolio_sharpe = self.calculate_sharpe_ratio(portfolio_returns)
        
        # Diversification ratio
        weighted_individual_vol = np.sum([risk.volatility * w for risk, w in zip(individual_risks, weights)])
        diversification_ratio = weighted_individual_vol / portfolio_volatility if portfolio_volatility > 0 else 1.0
        
        # Concentration risk
        concentration_risk = self.calculate_concentration_risk(weights)
        
        # Correlation risk
        correlation_risk = self.calculate_correlation_risk(all_returns)
        
        return {
            'portfolio_metrics': {
                'var_95': portfolio_var_95,
                'var_99': portfolio_var_99,
                'volatility': portfolio_volatility,
                'sharpe_ratio': portfolio_sharpe,
                'diversification_ratio': diversification_ratio,
                'concentration_risk': concentration_risk,
                'correlation_risk': correlation_risk
            },
            'individual_risks': [risk.to_dict() for risk in individual_risks],
            'weights': weights.tolist(),
            'total_certificates': len(certificates)
        }
    
    def check_risk_alerts(self, risk_metrics: RiskMetrics, 
                         certificate_id: str = None) -> List[RiskAlert]:
        """Verifica alert di rischio basati su soglie"""
        
        alerts = []
        
        # Check VaR thresholds
        if risk_metrics.var_95 < self.risk_thresholds['var_95']:
            alerts.append(RiskAlert(
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=RiskLevel.HIGH,
                message=f"VaR 95% sotto soglia: {risk_metrics.var_95:.2%} < {self.risk_thresholds['var_95']:.2%}",
                certificate_id=certificate_id,
                metric_value=risk_metrics.var_95,
                threshold_value=self.risk_thresholds['var_95']
            ))
        
        # Check volatility
        if risk_metrics.volatility > self.risk_thresholds['volatility']:
            alerts.append(RiskAlert(
                alert_type=AlertType.VOLATILITY_SPIKE,
                severity=RiskLevel.MEDIUM,
                message=f"Volatilità elevata: {risk_metrics.volatility:.2%} > {self.risk_thresholds['volatility']:.2%}",
                certificate_id=certificate_id,
                metric_value=risk_metrics.volatility,
                threshold_value=self.risk_thresholds['volatility']
            ))
        
        # Check concentration
        if risk_metrics.concentration_risk > self.risk_thresholds['concentration']:
            alerts.append(RiskAlert(
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=RiskLevel.MEDIUM,
                message=f"Rischio concentrazione alto: {risk_metrics.concentration_risk:.2%}",
                certificate_id=certificate_id,
                metric_value=risk_metrics.concentration_risk,
                threshold_value=self.risk_thresholds['concentration']
            ))
        
        # Check correlation
        if risk_metrics.correlation_risk > self.risk_thresholds['correlation']:
            alerts.append(RiskAlert(
                alert_type=AlertType.CORRELATION_BREAKDOWN,
                severity=RiskLevel.HIGH,
                message=f"Correlazioni elevate: {risk_metrics.correlation_risk:.2%}",
                certificate_id=certificate_id,
                metric_value=risk_metrics.correlation_risk,
                threshold_value=self.risk_thresholds['correlation']
            ))
        
        return alerts

# ========================================
# UNIFIED STRESS TEST ENGINE
# ========================================

class UnifiedStressTestEngine:
    """Stress Test Engine unificato - CONSOLIDA logiche multiple"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Scenari di stress predefiniti
        self.stress_scenarios = {
            'market_crash_2008': {
                'equity_shock': -0.40,
                'vol_shock': 3.0,
                'correlation_shock': 0.8,
                'credit_spread_shock': 0.05,
                'description': 'Scenario simile a crisi 2008'
            },
            'covid_crisis_2020': {
                'equity_shock': -0.35,
                'vol_shock': 4.0,
                'correlation_shock': 0.9,
                'liquidity_shock': 0.3,
                'description': 'Scenario simile a COVID-19'
            },
            'rate_shock_rising': {
                'rate_shock': 0.03,
                'vol_shock': 1.5,
                'duration_shock': 1.2,
                'description': 'Shock rialzo tassi di interesse'
            },
            'rate_shock_falling': {
                'rate_shock': -0.02,
                'vol_shock': 1.8,
                'deflation_shock': True,
                'description': 'Shock ribasso tassi / deflazione'
            },
            'volatility_explosion': {
                'vol_shock': 5.0,
                'correlation_breakdown': True,
                'description': 'Esplosione volatilità e breakdown correlazioni'
            },
            'liquidity_crisis': {
                'liquidity_shock': 0.5,
                'credit_spread_shock': 0.08,
                'vol_shock': 2.5,
                'description': 'Crisi di liquidità sistemica'
            },
            'black_swan': {
                'equity_shock': -0.60,
                'vol_shock': 6.0,
                'correlation_shock': 0.95,
                'credit_spread_shock': 0.10,
                'liquidity_shock': 0.7,
                'description': 'Evento tail risk estremo'
            }
        }
        
        self.logger.info("UnifiedStressTestEngine inizializzato con 7 scenari")
    
    def add_custom_scenario(self, scenario_name: str, scenario_params: Dict):
        """Aggiunge scenario di stress personalizzato"""
        self.stress_scenarios[scenario_name] = scenario_params
        self.logger.info(f"Scenario personalizzato '{scenario_name}' aggiunto")
    
    def apply_stress_scenario(self, market_data: Dict, scenario_name: str) -> Dict:
        """Applica scenario di stress ai dati di mercato"""
        
        if scenario_name not in self.stress_scenarios:
            raise ValueError(f"Scenario '{scenario_name}' non trovato")
        
        scenario = self.stress_scenarios[scenario_name]
        stressed_data = market_data.copy()
        
        self.logger.info(f"Applicazione scenario stress: {scenario_name}")
        
        # Shock equity
        if 'equity_shock' in scenario:
            for key in stressed_data:
                if any(term in key.lower() for term in ['price', 'equity', 'stock', 'spot']):
                    if isinstance(stressed_data[key], (list, np.ndarray)):
                        stressed_data[key] = [p * (1 + scenario['equity_shock']) for p in stressed_data[key]]
                    else:
                        stressed_data[key] = stressed_data[key] * (1 + scenario['equity_shock'])
        
        # Shock volatilità
        if 'vol_shock' in scenario:
            for key in stressed_data:
                if 'vol' in key.lower() or 'sigma' in key.lower():
                    if isinstance(stressed_data[key], (list, np.ndarray)):
                        stressed_data[key] = [v * scenario['vol_shock'] for v in stressed_data[key]]
                    else:
                        stressed_data[key] = stressed_data[key] * scenario['vol_shock']
        
        # Shock tassi
        if 'rate_shock' in scenario:
            for key in stressed_data:
                if any(term in key.lower() for term in ['rate', 'interest', 'yield']):
                    if isinstance(stressed_data[key], (list, np.ndarray)):
                        stressed_data[key] = [r + scenario['rate_shock'] for r in stressed_data[key]]
                    else:
                        stressed_data[key] = stressed_data[key] + scenario['rate_shock']
        
        # Shock correlazioni
        if 'correlation_shock' in scenario:
            for key in stressed_data:
                if 'corr' in key.lower():
                    if isinstance(stressed_data[key], np.ndarray):
                        corr_matrix = stressed_data[key]
                        n = corr_matrix.shape[0]
                        # Aumenta correlazioni off-diagonal
                        new_corr = np.eye(n)
                        for i in range(n):
                            for j in range(i+1, n):
                                new_corr[i,j] = new_corr[j,i] = scenario['correlation_shock']
                        stressed_data[key] = new_corr
        
        # Shock spread creditizi
        if 'credit_spread_shock' in scenario:
            for key in stressed_data:
                if any(term in key.lower() for term in ['spread', 'credit']):
                    if isinstance(stressed_data[key], (list, np.ndarray)):
                        stressed_data[key] = [s + scenario['credit_spread_shock'] for s in stressed_data[key]]
                    else:
                        stressed_data[key] = stressed_data[key] + scenario['credit_spread_shock']
        
        # Shock liquidità (riduce prezzi ulteriormente)
        if 'liquidity_shock' in scenario:
            liquidity_factor = 1 - scenario['liquidity_shock']
            for key in stressed_data:
                if any(term in key.lower() for term in ['price', 'value']):
                    if isinstance(stressed_data[key], (list, np.ndarray)):
                        stressed_data[key] = [p * liquidity_factor for p in stressed_data[key]]
                    else:
                        stressed_data[key] = stressed_data[key] * liquidity_factor
        
        return stressed_data
    
    def run_stress_test(self, certificate: CertificateBase, 
                       scenario_names: List[str] = None,
                       custom_scenarios: Dict = None) -> Dict:
        """Esegue stress test completo su certificato"""
        
        if scenario_names is None:
            scenario_names = list(self.stress_scenarios.keys())
        
        self.logger.info(f"Stress test su {certificate.specs.name} - {len(scenario_names)} scenari")
        
        results = {
            'certificate_info': {
                'name': certificate.specs.name,
                'isin': certificate.specs.isin,
                'type': certificate.specs.certificate_type
            },
            'base_scenario': {},
            'stress_scenarios': {},
            'summary': {}
        }
        
        try:
            # Scenario base
            if hasattr(certificate, 'parametri_mercato') and certificate.parametri_mercato:
                base_market_data = certificate.parametri_mercato
            else:
                # Crea dati base minimi
                base_market_data = {
                    'spot_prices': [certificate.get_current_spot()],
                    'volatilita': [certificate.market_data.volatility or 0.2],
                    'tasso_libero_rischio': certificate.risk_free_rate,
                    'correlazioni': np.eye(1)
                }
            
            # Pricing scenario base
            base_price = self._calculate_stressed_price(certificate, base_market_data)
            results['base_scenario'] = {
                'price': base_price,
                'market_data': base_market_data
            }
            
            # Stress scenari
            worst_case_loss = 0
            best_case_gain = 0
            scenario_results = {}
            
            for scenario_name in scenario_names:
                if scenario_name in self.stress_scenarios:
                    try:
                        # Applica stress
                        stressed_data = self.apply_stress_scenario(base_market_data, scenario_name)
                        
                        # Calcola prezzo stressed
                        stressed_price = self._calculate_stressed_price(certificate, stressed_data)
                        
                        # Calcola P&L
                        pnl = stressed_price - base_price
                        pnl_pct = (pnl / base_price * 100) if base_price != 0 else 0
                        
                        scenario_result = {
                            'stressed_price': stressed_price,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'scenario_description': self.stress_scenarios[scenario_name].get('description', ''),
                            'stressed_data': stressed_data
                        }
                        
                        scenario_results[scenario_name] = scenario_result
                        
                        # Track worst/best
                        if pnl_pct < worst_case_loss:
                            worst_case_loss = pnl_pct
                        if pnl_pct > best_case_gain:
                            best_case_gain = pnl_pct
                            
                        self.logger.debug(f"Scenario {scenario_name}: {pnl_pct:+.1f}%")
                        
                    except Exception as e:
                        self.logger.error(f"Errore scenario {scenario_name}: {e}")
                        scenario_results[scenario_name] = {'error': str(e)}
            
            # Aggiungi scenari custom se forniti
            if custom_scenarios:
                for custom_name, custom_params in custom_scenarios.items():
                    try:
                        self.add_custom_scenario(custom_name, custom_params)
                        stressed_data = self.apply_stress_scenario(base_market_data, custom_name)
                        stressed_price = self._calculate_stressed_price(certificate, stressed_data)
                        
                        pnl = stressed_price - base_price
                        pnl_pct = (pnl / base_price * 100) if base_price != 0 else 0
                        
                        scenario_results[custom_name] = {
                            'stressed_price': stressed_price,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'scenario_description': custom_params.get('description', 'Custom scenario'),
                            'custom': True
                        }
                        
                    except Exception as e:
                        self.logger.error(f"Errore scenario custom {custom_name}: {e}")
                        scenario_results[custom_name] = {'error': str(e)}
            
            results['stress_scenarios'] = scenario_results
            
            # Summary statistics
            valid_scenarios = [s for s in scenario_results.values() if 'error' not in s]
            if valid_scenarios:
                pnl_values = [s['pnl_pct'] for s in valid_scenarios]
                
                results['summary'] = {
                    'base_price': base_price,
                    'scenarios_tested': len(valid_scenarios),
                    'worst_case_loss_pct': worst_case_loss,
                    'best_case_gain_pct': best_case_gain,
                    'average_pnl_pct': np.mean(pnl_values),
                    'volatility_pnl_pct': np.std(pnl_values),
                    'scenarios_with_loss': len([p for p in pnl_values if p < 0]),
                    'max_loss_scenario': min(scenario_results.items(), key=lambda x: x[1].get('pnl_pct', 0))[0] if scenario_results else None
                }
            
            self.logger.info(f"Stress test completato - Worst case: {worst_case_loss:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Errore stress test: {e}")
            results['error'] = str(e)
        
        return results
    
    def _calculate_stressed_price(self, certificate, stressed_market_data):
        """Calcola prezzo del certificato sotto stress - SEZIONE CORRETTA"""
    #def _calculate_stressed_price(self, certificate: CertificateBase, 
    #                            stressed_market_data: Dict) -> float:
    #    """Calcola prezzo del certificato sotto stress"""
        
        try:
            if isinstance(certificate, (ExpressCertificate, PhoenixCertificate)):
                # Salva parametri originali
                original_params = getattr(certificate, 'parametri_mercato', {}).copy()
                
                # Applica parametri stressed
                certificate.parametri_mercato = stressed_market_data
                
                # Calcola pricing
                if hasattr(certificate, 'simulate_price_paths'):
                    paths = certificate.simulate_price_paths(n_simulations=3000)
                    
                    if isinstance(certificate, ExpressCertificate):
                        payoffs = certificate.calculate_express_payoffs(paths)
                    else:  # Phoenix
                        payoffs = certificate.calculate_phoenix_payoffs(paths)
                    
                    # Fair value
                    r = stressed_market_data.get('tasso_libero_rischio', 0.02)
                    if isinstance(certificate, ExpressCertificate):
                        tempi_uscita = payoffs.get('tempi_uscita', [certificate.get_time_to_maturity()] * len(payoffs['payoffs']))
                        valore_presente = payoffs['payoffs'] * np.exp(-r * np.array(tempi_uscita))
                    else:  # Phoenix
                        tempo_scadenza = len(certificate.coupon_schedule.payment_dates)
                        valore_presente = payoffs['payoffs'] * np.exp(-r * tempo_scadenza)
                    
                    stressed_price = np.mean(valore_presente)
                else:
                    # Fallback a pricing standard
                    stressed_price = certificate.calculate_price()
                
                # Ripristina parametri originali
                if original_params:
                    certificate.parametri_mercato = original_params
                
                return stressed_price
                
            else:
                # Certificati standard - aggiorna market data
                if certificate.market_data:
                    original_data = certificate.market_data
                    
                    # ✅ FIX: Crea nuovi market data stressed con STESSA LUNGHEZZA
                    from structural_cleanup import MarketData

                    # Usa i prezzi stressed ma mantieni la struttura originale #parte aggiunta
                    original_prices = original_data.prices
                    stressed_prices = stressed_market_data.get('spot_prices', original_prices)

                    # Se stressed_prices è una lista, prendi il primo elemento  #parte aggiunta
                    if isinstance(stressed_prices, list):
                        if len(stressed_prices) == 1:
                            # Caso: stressed_prices = [nuovo_prezzo]
                            # Crea serie temporale con stesso numero di punti
                            new_price = stressed_prices[0]
                            adjusted_prices = [new_price] * len(original_prices)
                        else:
                            # Caso: stressed_prices ha più elementi
                            # Adatta alla lunghezza originale
                            if len(stressed_prices) >= len(original_prices):
                                adjusted_prices = stressed_prices[:len(original_prices)]
                            else:
                                # Replica l'ultimo prezzo per raggiungere la lunghezza
                                adjusted_prices = stressed_prices + [stressed_prices[-1]] * (len(original_prices) - len(stressed_prices))
                    else:
                        # Caso: stressed_prices è un singolo valore
                        adjusted_prices = [stressed_prices] * len(original_prices)
                
                    stressed_data = MarketData(
                        dates=original_data.dates,  # ✅ Stessa lunghezza
                        prices=adjusted_prices,      # ✅ Stessa lunghezza
                        volatility=stressed_market_data.get('volatilita', [original_data.volatility])[0] if stressed_market_data.get('volatilita') else original_data.volatility,
                        risk_free_rate=stressed_market_data.get('tasso_libero_rischio', original_data.risk_free_rate),
                        dividend_yield=original_data.dividend_yield
                    )
                    
                    
#                    stressed_data = MarketData(
#                        dates=original_data.dates,
#                        prices=stressed_market_data.get('spot_prices', original_data.prices),
#                        volatility=stressed_market_data.get('volatilita', [original_data.volatility])[0] if stressed_market_data.get('volatilita') else original_data.volatility,
#                        risk_free_rate=stressed_market_data.get('tasso_libero_rischio', original_data.risk_free_rate),
#                        dividend_yield=original_data.dividend_yield
#                   )
                    
                    certificate.set_market_data(stressed_data)
                    stressed_price = certificate.calculate_price()
                    certificate.set_market_data(original_data)  # Ripristina
                    
                    return stressed_price
                else:
                    # Nessun market data disponibile
                    return certificate.specs.strike  # Fallback al strike
        
        except Exception as e:
            self.logger.error(f"Errore calcolo prezzo stressed: {e}")
            return certificate.specs.strike
    
    def run_portfolio_stress_test(self, certificates: List[CertificateBase],
                                 weights: List[float] = None,
                                 scenario_names: List[str] = None) -> Dict:
        """Esegue stress test su portfolio di certificati"""
        
        if weights is None:
            weights = [1.0 / len(certificates)] * len(certificates)
        
        if scenario_names is None:
            scenario_names = ['market_crash_2008', 'covid_crisis_2020', 'black_swan']
        
        self.logger.info(f"Portfolio stress test: {len(certificates)} certificati, {len(scenario_names)} scenari")
        
        results = {
            'portfolio_info': {
                'num_certificates': len(certificates),
                'weights': weights
            },
            'individual_results': {},
            'portfolio_results': {},
            'summary': {}
        }
        
        # Stress test individuali
        individual_results = {}
        for i, cert in enumerate(certificates):
            cert_id = f"{cert.specs.isin}_{i}"
            individual_results[cert_id] = self.run_stress_test(cert, scenario_names)
        
        results['individual_results'] = individual_results
        
        # Aggregazione portfolio
        portfolio_results = {}
        base_portfolio_value = 0
        
        for scenario in scenario_names + ['base_scenario']:
            scenario_portfolio_value = 0
            
            for i, cert_id in enumerate(individual_results.keys()):
                cert_result = individual_results[cert_id]
                
                if scenario == 'base_scenario':
                    cert_price = cert_result['base_scenario']['price']
                else:
                    if scenario in cert_result['stress_scenarios'] and 'error' not in cert_result['stress_scenarios'][scenario]:
                        cert_price = cert_result['stress_scenarios'][scenario]['stressed_price']
                    else:
                        cert_price = cert_result['base_scenario']['price']  # Fallback
                
                scenario_portfolio_value += cert_price * weights[i]
            
            if scenario == 'base_scenario':
                base_portfolio_value = scenario_portfolio_value
                portfolio_results[scenario] = {'value': scenario_portfolio_value}
            else:
                pnl = scenario_portfolio_value - base_portfolio_value
                pnl_pct = (pnl / base_portfolio_value * 100) if base_portfolio_value != 0 else 0
                
                portfolio_results[scenario] = {
                    'value': scenario_portfolio_value,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                }
        
        results['portfolio_results'] = portfolio_results
        
        # Summary portfolio
        stress_results = [r for k, r in portfolio_results.items() if k != 'base_scenario' and 'pnl_pct' in r]
        
        if stress_results:
            pnl_values = [r['pnl_pct'] for r in stress_results]
            
            results['summary'] = {
                'base_portfolio_value': base_portfolio_value,
                'worst_case_loss_pct': min(pnl_values),
                'best_case_gain_pct': max(pnl_values),
                'average_pnl_pct': np.mean(pnl_values),
                'portfolio_var_stress': np.percentile(pnl_values, 5)  # 5th percentile
            }
        
        self.logger.info("Portfolio stress test completato")
        return results

# ========================================
# UNIFIED COMPLIANCE CHECKER
# ========================================

class UnifiedComplianceChecker:
    """Sistema compliance unificato - CONSOLIDA logiche multiple"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Regole compliance consolidate
        self.compliance_rules = {
            # MiFID II
            'mifid_ii': {
                'max_risk_score': 4.5,
                'max_leverage': 5.0,
                'min_capital_protection': 0.8,  # Per retail
                'required_docs': ['kid', 'prospectus', 'risk_disclosure'],
                'suitability_check': True
            },
            
            # Basel III (per banche)
            'basel_iii': {
                'max_concentration_single': 0.25,
                'max_concentration_sector': 0.40,
                'min_liquidity_ratio': 1.0,
                'capital_adequacy_ratio': 0.08
            },
            
            # ESMA Guidelines
            'esma': {
                'max_complexity_score': 3.0,
                'transparency_requirements': True,
                'cost_disclosure': True,
                'performance_monitoring': True
            },
            
            # Regole interne personalizzabili
            'internal': {
                'max_single_exposure': 0.10,
                'min_rating': 'BBB-',
                'max_maturity_years': 10,
                'approved_asset_classes': ['bonds', 'deposits', 'structured_products']
            }
        }
        
        # Rating mapping
        self.rating_scores = {
            'AAA': 1, 'AA+': 2, 'AA': 2, 'AA-': 3,
            'A+': 3, 'A': 4, 'A-': 4,
            'BBB+': 5, 'BBB': 6, 'BBB-': 7,
            'BB+': 8, 'BB': 9, 'BB-': 10,
            'B+': 11, 'B': 12, 'B-': 13,
            'CCC+': 14, 'CCC': 15, 'CCC-': 16,
            'CC': 18, 'C': 20, 'D': 25
        }
        
        self.logger.info("UnifiedComplianceChecker inizializzato")
    
    def update_compliance_rules(self, rule_set: str, updates: Dict):
        """Aggiorna regole di compliance"""
        if rule_set in self.compliance_rules:
            self.compliance_rules[rule_set].update(updates)
            self.logger.info(f"Regole {rule_set} aggiornate")
        else:
            self.compliance_rules[rule_set] = updates
            self.logger.info(f"Nuovo set regole {rule_set} aggiunto")
    
    def check_certificate_compliance(self, certificate: CertificateBase,
                                   investor_profile: str = 'retail',
                                   rule_sets: List[str] = None) -> Dict:
        """Verifica compliance completa di un certificato"""
        
        if rule_sets is None:
            rule_sets = ['mifid_ii', 'internal']
        
        self.logger.info(f"Compliance check per {certificate.specs.name}")
        
        # Validazione input di sicurezza
        try:
            UnifiedValidator.validate_security_input(certificate.specs.name)
            UnifiedValidator.validate_security_input(certificate.specs.isin)
        except ValueError as e:
            return {
                'compliant': False,
                'violations': [f"Security validation failed: {e}"],
                'score': 0,
                'rule_sets_checked': rule_sets
            }
        
        violations = []
        warnings = []
        compliance_scores = {}
        
        # Calcola risk metrics per compliance
        risk_analyzer = UnifiedRiskAnalyzer()
        try:
            risk_metrics = risk_analyzer.analyze_certificate_risk(certificate)
        except Exception as e:
            risk_metrics = None
            warnings.append(f"Impossibile calcolare risk metrics: {e}")
        
        # Check ogni set di regole
        for rule_set in rule_sets:
            if rule_set not in self.compliance_rules:
                warnings.append(f"Rule set '{rule_set}' non trovato")
                continue
            
            rules = self.compliance_rules[rule_set]
            set_violations = []
            set_score = 100
            
            # MiFID II checks
            if rule_set == 'mifid_ii':
                mifid_violations, mifid_score = self._check_mifid_ii(
                    certificate, investor_profile, rules, risk_metrics
                )
                set_violations.extend(mifid_violations)
                set_score = min(set_score, mifid_score)
            
            # Basel III checks
            elif rule_set == 'basel_iii':
                basel_violations, basel_score = self._check_basel_iii(
                    certificate, rules, risk_metrics
                )
                set_violations.extend(basel_violations)
                set_score = min(set_score, basel_score)
            
            # ESMA checks
            elif rule_set == 'esma':
                esma_violations, esma_score = self._check_esma(
                    certificate, rules, risk_metrics
                )
                set_violations.extend(esma_violations)
                set_score = min(set_score, esma_score)
            
            # Internal checks
            elif rule_set == 'internal':
                internal_violations, internal_score = self._check_internal_rules(
                    certificate, rules, risk_metrics
                )
                set_violations.extend(internal_violations)
                set_score = min(set_score, internal_score)
            
            violations.extend(set_violations)
            compliance_scores[rule_set] = set_score
        
        # Score aggregato
        overall_score = np.mean(list(compliance_scores.values())) if compliance_scores else 0
        
        # Compliance status
        is_compliant = len(violations) == 0 and overall_score >= 70
        
        result = {
            'compliant': is_compliant,
            'violations': violations,
            'warnings': warnings,
            'score': overall_score,
            'scores_by_ruleset': compliance_scores,
            'rule_sets_checked': rule_sets,
            'investor_profile': investor_profile,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Compliance check completato - Score: {overall_score:.1f}, Compliant: {is_compliant}")
        return result
    
    def _check_mifid_ii(self, certificate: CertificateBase, investor_profile: str,
                       rules: Dict, risk_metrics) -> Tuple[List[str], float]:
        """Verifica regole MiFID II"""
        violations = []
        score = 100
        
        # Risk score check
        if risk_metrics and risk_metrics.volatility > rules['max_risk_score'] / 5:
            violations.append(f"Risk score troppo alto per profilo {investor_profile}")
            score -= 20
        
        # Leverage check
        leverage = getattr(certificate.specs, 'leverage', 1.0)
        if leverage > rules['max_leverage']:
            violations.append(f"Leverage {leverage} supera limite MiFID II {rules['max_leverage']}")
            score -= 15
        
        # Capital protection per retail
        if investor_profile == 'retail':
            protection_level = getattr(certificate.specs, 'protection_level', 0.0)
            # Fix: Gestisci caso None
            if protection_level is None:
                protection_level = 0.0
                
            if protection_level < rules['min_capital_protection']:
                violations.append("Protezione capitale insufficiente per investitore retail")
                score -= 25
        
        # Documentation check (semplificato)
        if rules.get('suitability_check', False):
            # In implementazione reale verificherebbe documentazione effettiva
            pass
        
        return violations, max(0, score)
    
    def _check_basel_iii(self, certificate: CertificateBase, rules: Dict,
                        risk_metrics) -> Tuple[List[str], float]:
        """Verifica regole Basel III"""
        violations = []
        score = 100
        
        # Concentration risk
        if risk_metrics and risk_metrics.concentration_risk > rules['max_concentration_single']:
            violations.append(f"Concentrazione singola oltre limite Basel III")
            score -= 20
        
        # Liquidity ratio
        if risk_metrics and risk_metrics.liquidity_risk > (1 - rules['min_liquidity_ratio']):
            violations.append("Ratio liquidità sotto requisiti Basel III")
            score -= 15
        
        return violations, max(0, score)
    
    def _check_esma(self, certificate: CertificateBase, rules: Dict,
                   risk_metrics) -> Tuple[List[str], float]:
        """Verifica linee guida ESMA"""
        violations = []
        score = 100
        
        # Complexity score (semplificato)
        complexity_score = self._calculate_complexity_score(certificate)
        if complexity_score > rules['max_complexity_score']:
            violations.append(f"Complessità prodotto oltre limiti ESMA")
            score -= 20
        
        # Transparency requirements
        if rules.get('transparency_requirements', False):
            # In implementazione reale verificherebbe presenza KID, etc.
            pass
        
        return violations, max(0, score)
    
    def _check_internal_rules(self, certificate: CertificateBase, rules: Dict,
                            risk_metrics) -> Tuple[List[str], float]:
        """Verifica regole interne"""
        violations = []
        score = 100
        
        # Single exposure limit
        exposure_pct = getattr(certificate, 'exposure_percentage', 0.05)  # Default 5%
        if exposure_pct > rules['max_single_exposure']:
            violations.append(f"Esposizione singola {exposure_pct:.1%} oltre limite interno")
            score -= 15
        
        # Maturity check
        time_to_maturity = certificate.get_time_to_maturity()
        if time_to_maturity > rules['max_maturity_years']:
            violations.append(f"Scadenza {time_to_maturity:.1f} anni oltre limite interno")
            score -= 10
        
        # Asset class check
        cert_type = certificate.specs.certificate_type
        approved_classes = rules['approved_asset_classes']
        if cert_type not in approved_classes:
            violations.append(f"Classe asset '{cert_type}' non approvata")
            score -= 25
        
        return violations, max(0, score)
    
    def _calculate_complexity_score(self, certificate: CertificateBase) -> float:
        """Calcola score di complessità del certificato"""
        
        complexity = 1.0  # Base score
        
        # Fattori di complessità
        cert_type = certificate.specs.certificate_type
        
        complexity_factors = {
            'bond': 1.0,
            'deposit': 0.5,
            'express': 2.5,
            'phoenix': 3.0,
            'barrier': 2.0,
            'autocallable': 2.8,
            'reverse_convertible': 3.2
        }
        
        complexity *= complexity_factors.get(cert_type, 2.0)
        
        # Barriere aggiungono complessità
        if hasattr(certificate.specs, 'barrier') and certificate.specs.barrier:
            complexity += 0.5
        
        # Underlying multipli
        if hasattr(certificate, 'underlying_assets'):
            n_assets = len(certificate.underlying_assets)
            if n_assets > 1:
                complexity += 0.3 * (n_assets - 1)
        
        # Memory features
        if hasattr(certificate, 'memory_coupon') and certificate.memory_coupon:
            complexity += 0.4
        
        return complexity
    
    def check_portfolio_compliance(self, certificates: List[CertificateBase],
                                 weights: List[float] = None,
                                 investor_profile: str = 'retail') -> Dict:
        """Verifica compliance di un portfolio"""
        
        if weights is None:
            weights = [1.0 / len(certificates)] * len(certificates)
        
        self.logger.info(f"Portfolio compliance check: {len(certificates)} certificati")
        
        # Check individuali
        individual_results = []
        total_violations = 0
        compliance_scores = []
        
        for i, cert in enumerate(certificates):
            cert_result = self.check_certificate_compliance(cert, investor_profile)
            cert_result['weight'] = weights[i]
            cert_result['certificate_name'] = cert.specs.name
            
            individual_results.append(cert_result)
            total_violations += len(cert_result['violations'])
            compliance_scores.append(cert_result['score'])
        
        # Aggregazione portfolio
        weighted_score = np.average(compliance_scores, weights=weights)
        portfolio_compliant = all(r['compliant'] for r in individual_results)
        
        # Check concentrazione portfolio
        concentration_violations = []
        max_weight = max(weights)
        if max_weight > 0.25:  # 25% max concentration
            concentration_violations.append(f"Concentrazione portfolio eccessiva: {max_weight:.1%}")
        
        # Diversificazione per tipo
        cert_types = [r['certificate_name'].split()[0] for r in individual_results]
        type_concentration = {}
        for cert_type in set(cert_types):
            type_weight = sum(w for w, t in zip(weights, cert_types) if t == cert_type)
            type_concentration[cert_type] = type_weight
            
            if type_weight > 0.50:  # 50% max per tipo
                concentration_violations.append(f"Concentrazione tipo '{cert_type}': {type_weight:.1%}")
        
        return {
            'portfolio_compliant': portfolio_compliant and len(concentration_violations) == 0,
            'portfolio_score': weighted_score,
            'total_violations': total_violations,
            'concentration_violations': concentration_violations,
            'individual_results': individual_results,
            'portfolio_metrics': {
                'num_certificates': len(certificates),
                'max_single_weight': max_weight,
                'type_concentration': type_concentration,
                'investor_profile': investor_profile
            },
            'timestamp': datetime.now().isoformat()
        }

# ========================================
# UNIFIED RISK DASHBOARD
# ========================================

class UnifiedRiskDashboard:
    """Dashboard unificato per monitoraggio rischi - CONSOLIDA logiche multiple"""
    
    def __init__(self):
        self.risk_analyzer = UnifiedRiskAnalyzer()
        self.stress_tester = UnifiedStressTestEngine()
        self.compliance_checker = UnifiedComplianceChecker()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Portfolio tracking
        self.portfolios = {}
        self.alerts = []
        self.monitoring_active = False
        
        # Configurazione alerting
        self.alert_config = {
            'var_95_threshold': -0.10,
            'volatility_threshold': 0.40,
            'compliance_threshold': 70,
            'concentration_threshold': 0.25
        }
        
        self.logger.info("UnifiedRiskDashboard inizializzato")
    
    def add_portfolio(self, portfolio_id: str, certificates: List[CertificateBase],
                     weights: List[float] = None, description: str = ""):
        """Aggiunge portfolio al monitoraggio"""
        
        if weights is None:
            weights = [1.0 / len(certificates)] * len(certificates)
        
        self.portfolios[portfolio_id] = {
            'certificates': certificates,
            'weights': weights,
            'description': description,
            'added_date': datetime.now(),
            'last_analysis': None,
            'current_alerts': []
        }
        
        self.logger.info(f"Portfolio '{portfolio_id}' aggiunto con {len(certificates)} certificati")
    
    def remove_portfolio(self, portfolio_id: str):
        """Rimuove portfolio dal monitoraggio"""
        if portfolio_id in self.portfolios:
            del self.portfolios[portfolio_id]
            self.logger.info(f"Portfolio '{portfolio_id}' rimosso")
    
    def run_comprehensive_analysis(self, portfolio_id: str = None) -> Dict:
        """Esegue analisi completa rischi per portfolio specifico o tutti"""
        
        if portfolio_id:
            if portfolio_id not in self.portfolios:
                raise ValueError(f"Portfolio '{portfolio_id}' non trovato")
            portfolios_to_analyze = {portfolio_id: self.portfolios[portfolio_id]}
        else:
            portfolios_to_analyze = self.portfolios
        
        self.logger.info(f"Analisi completa per {len(portfolios_to_analyze)} portfolio(s)")
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'portfolios_analyzed': len(portfolios_to_analyze),
            'portfolio_results': {},
            'system_alerts': [],
            'summary': {}
        }
        
        all_alerts = []
        total_risk_score = 0
        total_compliance_score = 0
        
        for pid, portfolio in portfolios_to_analyze.items():
            try:
                # Risk analysis
                portfolio_risk = self.risk_analyzer.analyze_portfolio_risk(
                    portfolio['certificates'], 
                    portfolio['weights']
                )
                
                # Stress testing
                stress_results = self.stress_tester.run_portfolio_stress_test(
                    portfolio['certificates'],
                    portfolio['weights'],
                    ['market_crash_2008', 'covid_crisis_2020']
                )
                
                # Compliance check
                compliance_results = self.compliance_checker.check_portfolio_compliance(
                    portfolio['certificates'],
                    portfolio['weights']
                )
                
                # Alert generation
                portfolio_alerts = self._generate_portfolio_alerts(
                    pid, portfolio_risk, stress_results, compliance_results
                )
                
                portfolio_result = {
                    'portfolio_id': pid,
                    'description': portfolio.get('description', ''),
                    'risk_analysis': portfolio_risk,
                    'stress_testing': stress_results,
                    'compliance_check': compliance_results,
                    'alerts': portfolio_alerts,
                    'risk_score': portfolio_risk['portfolio_metrics']['var_95'],
                    'compliance_score': compliance_results['portfolio_score']
                }
                
                results['portfolio_results'][pid] = portfolio_result
                
                # Update portfolio tracking
                self.portfolios[pid]['last_analysis'] = datetime.now()
                self.portfolios[pid]['current_alerts'] = portfolio_alerts
                
                # Aggregate for summary
                all_alerts.extend(portfolio_alerts)
                total_risk_score += abs(portfolio_risk['portfolio_metrics']['var_95'])
                total_compliance_score += compliance_results['portfolio_score']
                
            except Exception as e:
                self.logger.error(f"Errore analisi portfolio {pid}: {e}")
                results['portfolio_results'][pid] = {'error': str(e)}
        
        # System-wide alerts
        system_alerts = self._generate_system_alerts(results['portfolio_results'])
        results['system_alerts'] = system_alerts
        
        # Summary
        n_portfolios = len([r for r in results['portfolio_results'].values() if 'error' not in r])
        
        results['summary'] = {
            'total_portfolios': n_portfolios,
            'total_alerts': len(all_alerts),
            'critical_alerts': len([a for a in all_alerts if a.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]]),
            'average_risk_score': total_risk_score / n_portfolios if n_portfolios > 0 else 0,
            'average_compliance_score': total_compliance_score / n_portfolios if n_portfolios > 0 else 0,
            'system_health': self._calculate_system_health(results['portfolio_results'])
        }
        
        # Update global alerts
        self.alerts.extend(all_alerts)
        self.alerts.extend(system_alerts)
        
        self.logger.info(f"Analisi completa terminata - {len(all_alerts)} alerts generati")
        return results
    
    def _generate_portfolio_alerts(self, portfolio_id: str, risk_analysis: Dict,
                                 stress_results: Dict, compliance_results: Dict) -> List[RiskAlert]:
        """Genera alert specifici per portfolio"""
        
        alerts = []
        
        # Risk-based alerts
        portfolio_metrics = risk_analysis['portfolio_metrics']
        
        if portfolio_metrics['var_95'] < self.alert_config['var_95_threshold']:
            alerts.append(RiskAlert(
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=RiskLevel.HIGH,
                message=f"Portfolio {portfolio_id}: VaR 95% oltre soglia ({portfolio_metrics['var_95']:.2%})",
                certificate_id=portfolio_id,
                metric_value=portfolio_metrics['var_95'],
                threshold_value=self.alert_config['var_95_threshold']
            ))
        
        if portfolio_metrics['volatility'] > self.alert_config['volatility_threshold']:
            alerts.append(RiskAlert(
                alert_type=AlertType.VOLATILITY_SPIKE,
                severity=RiskLevel.MEDIUM,
                message=f"Portfolio {portfolio_id}: Volatilità elevata ({portfolio_metrics['volatility']:.2%})",
                certificate_id=portfolio_id,
                metric_value=portfolio_metrics['volatility'],
                threshold_value=self.alert_config['volatility_threshold']
            ))
        
        if portfolio_metrics['concentration_risk'] > self.alert_config['concentration_threshold']:
            alerts.append(RiskAlert(
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=RiskLevel.MEDIUM,
                message=f"Portfolio {portfolio_id}: Concentrazione eccessiva ({portfolio_metrics['concentration_risk']:.2%})",
                certificate_id=portfolio_id
            ))
        
        # Stress test alerts
        if 'summary' in stress_results and stress_results['summary'].get('worst_case_loss_pct', 0) < -30:
            alerts.append(RiskAlert(
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=RiskLevel.CRITICAL,
                message=f"Portfolio {portfolio_id}: Perdita stress test critica ({stress_results['summary']['worst_case_loss_pct']:.1f}%)",
                certificate_id=portfolio_id
            ))
        
        # Compliance alerts
        if compliance_results['portfolio_score'] < self.alert_config['compliance_threshold']:
            alerts.append(RiskAlert(
                alert_type=AlertType.COMPLIANCE_VIOLATION,
                severity=RiskLevel.HIGH,
                message=f"Portfolio {portfolio_id}: Score compliance sotto soglia ({compliance_results['portfolio_score']:.1f})",
                certificate_id=portfolio_id,
                metric_value=compliance_results['portfolio_score'],
                threshold_value=self.alert_config['compliance_threshold']
            ))
        
        return alerts
    
    def _generate_system_alerts(self, portfolio_results: Dict) -> List[RiskAlert]:
        """Genera alert a livello sistema"""
        
        system_alerts = []
        
        # Conteggio portfolio con problemi
        high_risk_portfolios = 0
        compliance_issues = 0
        
        for pid, result in portfolio_results.items():
            if 'error' in result:
                continue
            
            if result.get('risk_score', 0) < -0.15:  # VaR < -15%
                high_risk_portfolios += 1
            
            if result.get('compliance_score', 100) < 70:
                compliance_issues += 1
        
        total_portfolios = len([r for r in portfolio_results.values() if 'error' not in r])
        
        # Alert sistemici
        if high_risk_portfolios / total_portfolios > 0.3 if total_portfolios > 0 else False:
            system_alerts.append(RiskAlert(
                alert_type=AlertType.SYSTEM_ERROR,
                severity=RiskLevel.CRITICAL,
                message=f"Sistema: {high_risk_portfolios}/{total_portfolios} portfolio ad alto rischio"
            ))
        
        if compliance_issues / total_portfolios > 0.2 if total_portfolios > 0 else False:
            system_alerts.append(RiskAlert(
                alert_type=AlertType.COMPLIANCE_VIOLATION,
                severity=RiskLevel.HIGH,
                message=f"Sistema: {compliance_issues}/{total_portfolios} portfolio con problemi compliance"
            ))
        
        return system_alerts
    
    def _calculate_system_health(self, portfolio_results: Dict) -> str:
        """Calcola stato salute sistema"""
        
        valid_results = [r for r in portfolio_results.values() if 'error' not in r]
        if not valid_results:
            return "UNKNOWN"
        
        # Metriche aggregate
        avg_risk_score = np.mean([abs(r.get('risk_score', 0)) for r in valid_results])
        avg_compliance_score = np.mean([r.get('compliance_score', 100) for r in valid_results])
        
        total_alerts = sum(len(r.get('alerts', [])) for r in valid_results)
        critical_alerts = sum(len([a for a in r.get('alerts', []) if a.severity == RiskLevel.CRITICAL]) for r in valid_results)
        
        # Classificazione salute
        if critical_alerts > 0 or avg_risk_score > 0.20 or avg_compliance_score < 60:
            return "CRITICAL"
        elif total_alerts > len(valid_results) * 2 or avg_risk_score > 0.15 or avg_compliance_score < 75:
            return "WARNING"
        elif avg_risk_score > 0.10 or avg_compliance_score < 85:
            return "CAUTION"
        else:
            return "HEALTHY"
    
    def get_real_time_summary(self) -> Dict:
        """Restituisce summary real-time dello stato sistema"""
        
        current_time = datetime.now()
        
        # Alert attivi (ultimi 24h)
        recent_alerts = [a for a in self.alerts if 
                        (current_time - a.timestamp).total_seconds() < 86400]
        
        # Portfolio status
        portfolio_status = {}
        for pid, portfolio in self.portfolios.items():
            last_analysis = portfolio.get('last_analysis')
            current_alerts = portfolio.get('current_alerts', [])
            
            if last_analysis:
                hours_since_analysis = (current_time - last_analysis).total_seconds() / 3600
                status = "STALE" if hours_since_analysis > 24 else "CURRENT"
            else:
                status = "NEVER_ANALYZED"
            
            portfolio_status[pid] = {
                'status': status,
                'last_analysis': last_analysis.isoformat() if last_analysis else None,
                'active_alerts': len(current_alerts),
                'critical_alerts': len([a for a in current_alerts if a.severity == RiskLevel.CRITICAL])
            }
        
        return {
            'timestamp': current_time.isoformat(),
            'total_portfolios': len(self.portfolios),
            'recent_alerts_24h': len(recent_alerts),
            'critical_alerts_24h': len([a for a in recent_alerts if a.severity == RiskLevel.CRITICAL]),
            'portfolio_status': portfolio_status,
            'system_health': self._calculate_system_health({
                pid: {'risk_score': -0.05, 'compliance_score': 85, 'alerts': p.get('current_alerts', [])}
                for pid, p in self.portfolios.items()
            }),
            'monitoring_active': self.monitoring_active
        }
    
    def generate_risk_report(self, portfolio_id: str = None, 
                           include_details: bool = True) -> str:
        """Genera report di rischio testuale"""
        
        if portfolio_id and portfolio_id not in self.portfolios:
            return f"ERRORE: Portfolio '{portfolio_id}' non trovato"
        
        # Esegui analisi completa
        analysis = self.run_comprehensive_analysis(portfolio_id)
        
        # Genera report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("UNIFIED RISK MANAGEMENT REPORT")
        report_lines.append(f"Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        
        # Summary
        summary = analysis['summary']
        report_lines.append(f"\nSUMMARY ESECUTIVO:")
        report_lines.append(f"  Portfolio analizzati: {summary['total_portfolios']}")
        report_lines.append(f"  Alert totali: {summary['total_alerts']}")
        report_lines.append(f"  Alert critici: {summary['critical_alerts']}")
        report_lines.append(f"  Risk score medio: {summary['average_risk_score']:.2%}")
        report_lines.append(f"  Compliance score medio: {summary['average_compliance_score']:.1f}")
        report_lines.append(f"  Stato sistema: {summary['system_health']}")
        
        # Portfolio details
        if include_details:
            for pid, result in analysis['portfolio_results'].items():
                if 'error' in result:
                    report_lines.append(f"\n❌ PORTFOLIO {pid}: ERRORE - {result['error']}")
                    continue
                
                report_lines.append(f"\n📊 PORTFOLIO: {pid}")
                report_lines.append(f"   Descrizione: {result['description']}")
                
                # Risk metrics
                risk = result['risk_analysis']['portfolio_metrics']
                report_lines.append(f"   VaR 95%: {risk['var_95']:.2%}")
                report_lines.append(f"   Volatilità: {risk['volatility']:.2%}")
                report_lines.append(f"   Diversification Ratio: {risk['diversification_ratio']:.2f}")
                
                # Stress test
                if 'summary' in result['stress_testing']:
                    stress = result['stress_testing']['summary']
                    report_lines.append(f"   Worst Case Loss: {stress['worst_case_loss_pct']:.1f}%")
                
                # Compliance
                compliance = result['compliance_check']
                report_lines.append(f"   Compliance Score: {compliance['portfolio_score']:.1f}")
                report_lines.append(f"   Compliance Status: {'✅' if compliance['portfolio_compliant'] else '❌'}")
                
                # Alerts
                alerts = result['alerts']
                if alerts:
                    report_lines.append(f"   🚨 ALERT ({len(alerts)}):")
                    for alert in alerts[:3]:  # Top 3
                        severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(alert.severity.value.upper(), "🔵")
                        report_lines.append(f"     {severity_icon} {alert.message}")
                    if len(alerts) > 3:
                        report_lines.append(f"     ... e altri {len(alerts)-3} alert")
                else:
                    report_lines.append(f"   ✅ Nessun alert attivo")
        
        # System alerts
        system_alerts = analysis['system_alerts']
        if system_alerts:
            report_lines.append(f"\n🚨 ALERT DI SISTEMA ({len(system_alerts)}):")
            for alert in system_alerts:
                report_lines.append(f"   🔴 {alert.message}")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("FINE REPORT")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def start_monitoring(self, interval_minutes: int = 60):
        """Avvia monitoraggio automatico (simulato)"""
        self.monitoring_active = True
        self.monitoring_interval = interval_minutes
        self.logger.info(f"Monitoraggio automatico avviato (intervallo: {interval_minutes} min)")
    
    def stop_monitoring(self):
        """Ferma monitoraggio automatico"""
        self.monitoring_active = False
        self.logger.info("Monitoraggio automatico fermato")

# ========================================
# TESTING E VALIDAZIONE CONSOLIDATI
# ========================================

def test_consolidated_risk_system():
    """Test completo sistema risk consolidato"""
    
    print("=" * 80)
    print("TEST SISTEMA RISK CONSOLIDATO")
    print("=" * 80)
    
    errors = []
    
    try:
        # Setup certificati di test
        from unified_certificates import create_sample_express_certificate, create_sample_phoenix_certificate
        
        print("1. Test UnifiedRiskAnalyzer...")
        
        # Crea certificati
        express_cert = create_sample_express_certificate()
        phoenix_cert = create_sample_phoenix_certificate()
        
        # Risk analyzer
        risk_analyzer = UnifiedRiskAnalyzer()
        
        # Analisi risk Express
        risk_express = risk_analyzer.analyze_certificate_risk(express_cert, n_simulations=2000)
        print(f"   ✅ Express Risk Analysis - VaR 95%: {risk_express.var_95:.2%}")
        
        # Analisi risk Phoenix
       
        risk_phoenix = risk_analyzer.analyze_certificate_risk(phoenix_cert, n_simulations=2000)
        print(f"   ✅ Phoenix Risk Analysis - VaR 95%: {risk_phoenix.var_95:.2%}")
        
        # Portfolio risk analysis
        portfolio_risk = risk_analyzer.analyze_portfolio_risk([express_cert, phoenix_cert], [0.6, 0.4])
        print(f"   ✅ Portfolio Risk - VaR 95%: {portfolio_risk['portfolio_metrics']['var_95']:.2%}")
        
        print("2. Test UnifiedStressTestEngine...")
        
        # Stress test engine
        stress_tester = UnifiedStressTestEngine()
        
        # Stress test Express
        stress_express = stress_tester.run_stress_test(
            express_cert, 
            ['market_crash_2008', 'covid_crisis_2020', 'black_swan']
        )
        print(f"   ✅ Express Stress Test - Worst case: {stress_express['summary']['worst_case_loss_pct']:.1f}%")
        
        # Portfolio stress test
        portfolio_stress = stress_tester.run_portfolio_stress_test(
            [express_cert, phoenix_cert], 
            [0.6, 0.4],
            ['market_crash_2008', 'black_swan']
        )
        print(f"   ✅ Portfolio Stress Test - Worst case: {portfolio_stress['summary']['worst_case_loss_pct']:.1f}%")
        
        print("3. Test UnifiedComplianceChecker...")
        
        # Compliance checker
        compliance_checker = UnifiedComplianceChecker()
        
        # Compliance Express
        compliance_express = compliance_checker.check_certificate_compliance(
            express_cert, 'retail', ['mifid_ii', 'internal']
        )
        print(f"   ✅ Express Compliance - Score: {compliance_express['score']:.1f}, Compliant: {compliance_express['compliant']}")
        
        # Portfolio compliance
        portfolio_compliance = compliance_checker.check_portfolio_compliance(
            [express_cert, phoenix_cert], [0.6, 0.4], 'retail'
        )
        print(f"   ✅ Portfolio Compliance - Score: {portfolio_compliance['portfolio_score']:.1f}")
        
        print("4. Test UnifiedRiskDashboard...")
        
        # Risk dashboard
        dashboard = UnifiedRiskDashboard()
        
        # Add portfolio
        dashboard.add_portfolio('TEST_PORTFOLIO', [express_cert, phoenix_cert], [0.6, 0.4], 'Test Portfolio')
        
        # Run comprehensive analysis
        comprehensive_analysis = dashboard.run_comprehensive_analysis('TEST_PORTFOLIO')
        print(f"   ✅ Dashboard Analysis - Alerts: {comprehensive_analysis['summary']['total_alerts']}")
        
        # Real-time summary
        rt_summary = dashboard.get_real_time_summary()
        print(f"   ✅ Real-time Summary - System Health: {rt_summary['system_health']}")
        
        print("5. Test Alert Generation...")
        
        # Test alerts
        alerts = risk_analyzer.check_risk_alerts(risk_express, 'EXPRESS_TEST')
        print(f"   ✅ Risk Alerts Generated: {len(alerts)}")
        
        for alert in alerts[:2]:  # Show first 2
            print(f"      - {alert.alert_type.value}: {alert.message}")
        
        print("6. Test Report Generation...")
        
        # Generate comprehensive report
        full_report = dashboard.generate_risk_report('TEST_PORTFOLIO', include_details=True)
        print("   ✅ Full Risk Report Generated")
        
        # Show excerpt
        report_lines = full_report.split('\n')
        print("   📄 Report Excerpt:")
        for line in report_lines[5:10]:  # Show 5 lines
            print(f"      {line}")
        
        print("7. Test Performance...")
        
        # Performance test
        import time
        start_time = time.time()
        
        # Multiple risk analyses
        for _ in range(5):
            risk_analyzer.analyze_certificate_risk(express_cert, n_simulations=1000)
        
        end_time = time.time()
        performance_time = end_time - start_time
        print(f"   ✅ Performance Test - 5 analisi in {performance_time:.2f}s")
        
        print("8. Test Cache System...")
        
        # Test cache
        start_time = time.time()
        risk_analyzer.analyze_certificate_risk(express_cert, n_simulations=1000)  # Should use cache
        cache_time = time.time() - start_time
        print(f"   ✅ Cache Test - Analisi cached in {cache_time:.3f}s")
        
    except Exception as e:
        print(f"   ❌ Errore durante test: {e}")
        errors.append(str(e))
        import traceback
        traceback.print_exc()
    
    # Riepilogo
    print("\n" + "=" * 80)
    print("RIEPILOGO TEST RISK SYSTEM CONSOLIDATION")
    print("=" * 80)
    
    if not errors:
        print("🎉 TUTTI I TEST PASSATI - RISK SYSTEM CONSOLIDATION COMPLETATO!")
        print("\n✅ Sistemi consolidati:")
        print("   - UnifiedRiskAnalyzer (VaR, CVaR, Sharpe, Sortino, + metriche avanzate)")
        print("   - UnifiedStressTestEngine (7 scenari predefiniti + custom)")
        print("   - UnifiedComplianceChecker (MiFID II, Basel III, ESMA, Internal)")
        print("   - UnifiedRiskDashboard (Portfolio monitoring, alerting, reporting)")
        print("   - Alert System (6 tipi alert, severity levels)")
        print("   - Cache System (Performance optimization)")
        print("   - Real-time Monitoring (Portfolio tracking)")
        
        print("\n🚀 PRONTO PER STEP 4: Demo System Unification")
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
    print("RISK SYSTEM CONSOLIDATION - Sistema Certificati Finanziari")
    print("Versione Consolidata - Risk Management Unificato")
    print("=" * 80)
    
    success = test_consolidated_risk_system()
    
    if success:
        print("\n" + "🎯 RISK SYSTEM CONSOLIDATION COMPLETATO CON SUCCESSO!")
        print("\nSISTEMI UNIFICATI DISPONIBILI:")
        print("✅ UnifiedRiskAnalyzer - Risk analysis completo")
        print("✅ UnifiedStressTestEngine - Stress testing avanzato") 
        print("✅ UnifiedComplianceChecker - Compliance multi-framework")
        print("✅ UnifiedRiskDashboard - Dashboard monitoring completo")
        print("✅ Alert System - Sistema alerting real-time")
        print("✅ Portfolio Management - Gestione portfolio integrata")
        
        print(f"\n📊 STATISTICHE:")
        print(f"   Classi risk unificate: 4")
        print(f"   Scenari stress: 7 predefiniti + custom")
        print(f"   Framework compliance: 4 (MiFID II, Basel III, ESMA, Internal)")
        print(f"   Tipi alert: 6")
        print(f"   Metriche risk: 14")
        
        print(f"\n⏭️  PROSSIMO STEP: Demo System Unification")
        
    else:
        print("\n❌ ERRORI NEL RISK SYSTEM CONSOLIDATION - VERIFICARE LOG")
