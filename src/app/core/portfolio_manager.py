# ========================================
# PORTFOLIO MANAGEMENT SYSTEM v15.0
# Sistema Certificati Finanziari - Gestione Portafogli
# ========================================
# File: portfolio_manager.py
# Timestamp: 2025-06-16 15:00:00
# Gestione portafogli multi-certificato con analytics avanzate
# ========================================

"""
PORTFOLIO MANAGEMENT SYSTEM:

1. Creazione e gestione portafogli multipli
2. Aggregazione rischi a livello portfolio
3. Diversificazione e correlation analysis  
4. Performance tracking multi-certificato
5. Portfolio optimization e rebalancing
6. Dashboard consolidato

INTEGRAZIONE:
✅ Sistema certificati esistente
✅ Risk analytics unificato
✅ Excel reporting avanzato
✅ GUI integration ready
"""

# ==========================================================
# NOME FILE: portfolio_manager.py
# SCOPO: Gestione dei portafogli multi-certificato, analytics e dashboard
# AUTORE: Mario Rossi
# DATA CREAZIONE: 2024-06-22
# ULTIMA MODIFICA: 2024-06-22
# VERSIONE: 1.0
# ==========================================================
#
# DESCRIZIONE:
# Questo modulo implementa la logica per la creazione, gestione, analisi e reporting
# di portafogli composti da certificati finanziari. Include classi per la gestione
# delle posizioni, metriche aggregate, ottimizzazione e integrazione con la GUI.
#
# PRINCIPALI CLASSI/FUNZIONI:
# - PortfolioManager: Gestione CRUD portafogli, posizioni, metriche e reporting
# - PortfolioGUIManager: Integrazione GUI per dashboard e operazioni utente
#
# DIPENDENZE:
# - pandas, numpy, tkinter, moduli interni (structural_cleanup, unified_certificates, ecc.)
#
# NOTE:
# - Da completare la serializzazione completa delle posizioni
# ==========================================================

# ==========================================================
# RIEPILOGO CONTENUTO FILE:
# - @dataclass: PortfolioConfig, PortfolioMetrics
# - Classe principale: PortfolioManager (gestione portafogli, posizioni, analytics, reporting)
# - Classe: PortfolioGUIManager (integrazione GUI)
# - Funzioni di test/demo: test_portfolio_system
# ==========================================================

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import tkinter as tk
from tkinter import ttk, messagebox 

# Import dal sistema esistente
from app.core.structural_cleanup import (
    CertificateSpecs, MarketData, UnifiedValidator,
    DateUtils, logger
)

from app.core.unified_certificates import (
    CertificateBase, ExpressCertificate, PhoenixCertificate,
    UnifiedCertificateAnalyzer, CertificateType
)

from app.core.consolidated_risk_system import (
    UnifiedRiskAnalyzer, RiskMetrics, RiskLevel, AlertType
)

from app.core.real_certificate_integration import (
    RealCertificateImporter, EnhancedExcelExporter
)

# ========================================
# PORTFOLIO DATA STRUCTURES
# ========================================

class PortfolioType(Enum):
    """Tipi di portafoglio"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    INCOME_FOCUSED = "income_focused"
    CAPITAL_PROTECTION = "capital_protection"
    GROWTH = "growth"
    INCOME = "income"
    ABSOLUTE_RETURN = "absolute_return"
    CUSTOM = "custom"

class RebalancingFrequency(Enum):
    """Frequenza di ribilanciamento"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    MANUAL = "manual"

@dataclass
class PortfolioPosition:
    """Rappresenta una posizione in portafoglio"""
    certificate_id: str
    certificate: CertificateBase
    nominal_amount: float
    market_value: float
    fair_value: float
    weight_target: float
    weight_current: float
    entry_date: datetime
    entry_price: float
    current_price: float
    unrealized_pnl: float
    risk_contribution: float
    
    def __post_init__(self):
        """Calcoli automatici"""
        self.unrealized_pnl = self.market_value - (self.nominal_amount * self.entry_price / 100)
        self.weight_current = 0.0  # Sarà calcolato dal portfolio

@dataclass  
class PortfolioConstraints:
    """Vincoli di portafoglio"""
    max_single_position: float = 0.20  # 20% max per singola posizione
    max_issuer_exposure: float = 0.30   # 30% max per singolo emittente
    max_sector_exposure: float = 0.40   # 40% max per singolo settore
    max_currency_exposure: float = 0.80 # 80% max per singola valuta
    min_diversification: int = 5        # Minimo 5 posizioni
    max_correlation: float = 0.70       # Correlazione massima
    min_duration: float = 0.5           # Durata minima anni
    max_duration: float = 10.0          # Durata massima anni
    target_return: float = 0.08         # Target return 8%
    max_volatility: float = 0.15        # Volatilità massima 15%
    max_var_95: float = 0.10           # VaR 95% massimo 10%

@dataclass
class PortfolioConfig:
    """Configurazione portafoglio"""
    name: str
    description: str
    portfolio_type: PortfolioType
    base_currency: str = "EUR"
    inception_date: datetime = field(default_factory=datetime.now)
    target_size: float = 1000000.0  # 1M EUR default
    constraints: PortfolioConstraints = field(default_factory=PortfolioConstraints)
    rebalancing_frequency: RebalancingFrequency = RebalancingFrequency.QUARTERLY
    auto_rebalancing: bool = False
    benchmark: Optional[str] = None
    manager: str = "System"
    risk_profile: str = "moderate"

# ========================================
# PORTFOLIO ANALYTICS
# ========================================

@dataclass
class PortfolioMetrics:
    """Metriche aggregate di portafoglio"""
    total_market_value: float
    total_fair_value: float
    total_nominal: float
    total_pnl: float
    total_return_pct: float
    fair_value_gap: float
    
    # Risk metrics
    portfolio_volatility: float
    portfolio_var_95: float
    portfolio_expected_shortfall: float
    portfolio_beta: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    
    # Diversification
    number_positions: int
    effective_diversification: float
    concentration_index: float
    correlation_average: float
    
    # Sector/Geography exposure
    sector_exposure: Dict[str, float]
    currency_exposure: Dict[str, float]
    issuer_exposure: Dict[str, float]
    maturity_distribution: Dict[str, float]
    
    # Performance attribution
    security_selection: float
    asset_allocation: float
    interaction_effect: float
    
    timestamp: datetime = field(default_factory=datetime.now)

# ========================================
# PORTFOLIO MANAGER CORE
# ========================================

class PortfolioManager:
    """Portfolio Manager principale - gestione portafogli multi-certificato"""
    
    def __init__(self, base_dir: str = "D:/Doc/File python/Finanza/Certificates/Revisione2/src/app/data"):
        # base_dir deve essere la directory "configs", NON la directory superiore
        self.base_dir = Path(base_dir)
        # Rimuovi eventuale aggiunta di "configs" qui sotto
        self.portfolios_file = self.base_dir / "portfolios.json"
        self.positions_file = self.base_dir / "positions.json"
        
        # Assicura directory
        self.portfolios_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Storage
        self.portfolios: Dict[str, PortfolioConfig] = {}
        self.positions: Dict[str, List[PortfolioPosition]] = {}
        self.analytics: Dict[str, PortfolioMetrics] = {}
        
        # Integrazione sistema esistente
        self.certificate_importer = RealCertificateImporter()
        self.risk_analyzer = UnifiedRiskAnalyzer()
        self.excel_exporter = EnhancedExcelExporter(str(self.base_dir))
        
        self.logger = logging.getLogger(f"{__name__}.PortfolioManager")
        
        # Carica dati esistenti
        self._load_portfolios()
        self._load_positions()
        
        # Migrazione da vecchio formato (una tantum)
        # self.migrate_from_old_enhanced_certificates()
        
        self.logger.info("Portfolio Manager inizializzato")
    
    def migrate_from_old_enhanced_certificates(self, old_path=None):
        """
        Migra i dati da enhanced_certificates.json (vecchio formato) a
        portfolios.json e positions.json (nuovo formato).
        """
        if old_path is None:
            old_path = self.base_dir / "configs/enhanced_certificates.json"
        if not Path(old_path).exists():
            self.logger.info(f"Nessun file da migrare: {old_path}")
            return False

        with open(old_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        migrated_portfolios = {}
        migrated_positions = {}

        for portfolio_id, positions in data.items():
            # Se positions è una lista, è un portafoglio
            if isinstance(positions, list):
                # Crea una configurazione minimale se non esiste già
                migrated_portfolios[portfolio_id] = {
                    "name": portfolio_id,
                    "description": "",
                    "portfolio_type": "custom",
                    "base_currency": "EUR",
                    "inception_date": "2024-01-01T00:00:00",
                    "target_size": 100000.0,
                    "constraints": {
                        "max_single_position": 0.20,
                        "max_issuer_exposure": 0.30,
                        "max_sector_exposure": 0.40,
                        "max_currency_exposure": 0.80,
                        "min_diversification": 5,
                        "max_correlation": 0.70,
                        "min_duration": 0.5,
                        "max_duration": 10.0,
                        "target_return": 0.08,
                        "max_volatility": 0.15,
                        "max_var_95": 0.10
                    },
                    "rebalancing_frequency": "quarterly",
                    "auto_rebalancing": False,
                    "benchmark": None,
                    "manager": "System",
                    "risk_profile": "moderate"
                }
                migrated_positions[portfolio_id] = positions

        # Salva i nuovi file solo se non esistono già
        if not self.portfolios_file.exists():
            with open(self.portfolios_file, "w", encoding="utf-8") as f:
                json.dump(migrated_portfolios, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Migrati {len(migrated_portfolios)} portafogli in {self.portfolios_file}")
        else:
            self.logger.info(f"File {self.portfolios_file} già esistente, migrazione non sovrascrive.")

        if not self.positions_file.exists():
            with open(self.positions_file, "w", encoding="utf-8") as f:
                json.dump(migrated_positions, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Migrate posizioni in {self.positions_file}")
        else:
            self.logger.info(f"File {self.positions_file} già esistente, migrazione non sovrascrive.")

        return True

    # ========================================
    # PORTFOLIO CREATION & MANAGEMENT
    # ========================================
    
    def create_portfolio(self, config: PortfolioConfig, overwrite: bool = False) -> str:
        """Crea nuovo portafoglio v15.1 con gestione sovrascrittura"""
        
        portfolio_id = f"PF_{config.name.upper().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        
        # Validazione
        if portfolio_id in self.portfolios:
            if overwrite:
                print(f"⚠️ Sovrascrittura portfolio esistente: {portfolio_id}")
            else:
                # Genera ID unico per test
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                portfolio_id = f"PF_{config.name.upper().replace(' ', '_')}_{timestamp}"
                print(f"🔄 Portfolio ID aggiornato per evitare conflitto: {portfolio_id}")            
        
        # Salva configurazione
        self.portfolios[portfolio_id] = config
        self.positions[portfolio_id] = []
        
        # Salva su disco
        self._save_portfolios()
        
        self.logger.info(f"Portfolio {portfolio_id} creato: {config.name}")
        return portfolio_id
    
    def add_position(self, portfolio_id: str, certificate_id: str, 
                    certificate: CertificateBase, nominal_amount: float,
                    entry_price: float = 100.0) -> None:
        """Aggiunge posizione a portafoglio"""
        
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} non trovato")
        
        # Calcola valori
        market_value = nominal_amount * entry_price / 100
        
        # Calcola fair value se possibile
        try:
            analyzer = UnifiedCertificateAnalyzer(certificate)
            fair_result = analyzer.calculate_fair_value(n_simulations=5000)
            fair_value = nominal_amount * fair_result['fair_value'] / 100
        except Exception as e:
            self.logger.warning(f"Fair value non calcolabile per {certificate_id}: {e}")
            fair_value = market_value
        
        # Crea posizione
        position = PortfolioPosition(
            certificate_id=certificate_id,
            certificate=certificate,
            nominal_amount=nominal_amount,
            market_value=market_value,
            fair_value=fair_value,
            weight_target=0.0,  # Da calcolare
            weight_current=0.0,  # Da calcolare
            entry_date=datetime.now(),
            entry_price=entry_price,
            current_price=entry_price,
            unrealized_pnl=0.0,
            risk_contribution=0.0
        )
        
        # Aggiunge al portafoglio
        self.positions[portfolio_id].append(position)
        
        # Ricalcola pesi
        self._update_portfolio_weights(portfolio_id)
        
        # Salva
        self._save_positions()
        
        self.logger.info(f"Posizione {certificate_id} aggiunta a {portfolio_id}: €{nominal_amount:,.0f}")
    
    def remove_position(self, portfolio_id: str, certificate_id: str) -> None:
        """Rimuove posizione da portafoglio"""
        
        if portfolio_id not in self.positions:
            raise ValueError(f"Portfolio {portfolio_id} non trovato")
        
        # Trova e rimuovi posizione
        positions = self.positions[portfolio_id]
        self.positions[portfolio_id] = [pos for pos in positions if pos.certificate_id != certificate_id]
        
        # Ricalcola pesi
        self._update_portfolio_weights(portfolio_id)
        
        # Salva
        self._save_positions()
        
        self.logger.info(f"Posizione {certificate_id} rimossa da {portfolio_id}")
    
    def update_position_prices(self, portfolio_id: str, price_updates: Dict[str, float]) -> None:
        """Aggiorna prezzi posizioni"""
        
        if portfolio_id not in self.positions:
            raise ValueError(f"Portfolio {portfolio_id} non trovato")
        
        updated_count = 0
        
        for position in self.positions[portfolio_id]:
            if position.certificate_id in price_updates:
                new_price = price_updates[position.certificate_id]
                
                # Aggiorna prezzi e valori
                position.current_price = new_price
                position.market_value = position.nominal_amount * new_price / 100
                position.unrealized_pnl = position.market_value - (position.nominal_amount * position.entry_price / 100)
                
                updated_count += 1
        
        # Ricalcola pesi e metriche
        self._update_portfolio_weights(portfolio_id)
        
        # Salva
        self._save_positions()
        
        self.logger.info(f"Aggiornati prezzi per {updated_count} posizioni in {portfolio_id}")
    
    # ========================================
    # PORTFOLIO ANALYTICS
    # ========================================
    
    def calculate_portfolio_metrics(self, portfolio_id: str) -> PortfolioMetrics:
        """Calcola metriche complete di portafoglio"""
        
        if portfolio_id not in self.positions:
            raise ValueError(f"Portfolio {portfolio_id} non trovato")
        
        positions = self.positions[portfolio_id]
        
        if not positions:
            # Portfolio vuoto
            return self._empty_portfolio_metrics()
        
        self.logger.info(f"Calcolo metriche per portfolio {portfolio_id} con {len(positions)} posizioni")
        
        # Metriche base
        total_market_value = sum(pos.market_value for pos in positions)
        total_fair_value = sum(pos.fair_value for pos in positions)
        total_nominal = sum(pos.nominal_amount for pos in positions)
        total_pnl = sum(pos.unrealized_pnl for pos in positions)
        
        total_return_pct = total_pnl / (total_nominal * sum(pos.entry_price for pos in positions) / len(positions) / 100) if positions else 0
        fair_value_gap = (total_fair_value - total_market_value) / total_market_value if total_market_value > 0 else 0
        
        # Risk metrics (semplificato per ora)
        try:
            risk_metrics = self._calculate_portfolio_risk(positions)
        except Exception as e:
            self.logger.warning(f"Errore calcolo risk metrics: {e}")
            risk_metrics = self._default_risk_metrics()
        
        # Diversification metrics
        diversification_metrics = self._calculate_diversification_metrics(positions)
        
        # Exposure analysis
        exposure_metrics = self._calculate_exposure_metrics(positions)
        
        # Crea metriche complete
        metrics = PortfolioMetrics(
            total_market_value=total_market_value,
            total_fair_value=total_fair_value,
            total_nominal=total_nominal,
            total_pnl=total_pnl,
            total_return_pct=total_return_pct,
            fair_value_gap=fair_value_gap,
            
            # Risk (da calcolo avanzato)
            portfolio_volatility=risk_metrics['volatility'],
            portfolio_var_95=risk_metrics['var_95'],
            portfolio_expected_shortfall=risk_metrics['expected_shortfall'],
            portfolio_beta=risk_metrics['beta'],
            sharpe_ratio=risk_metrics['sharpe_ratio'],
            sortino_ratio=risk_metrics['sortino_ratio'],
            max_drawdown=risk_metrics['max_drawdown'],
            
            # Diversification
            number_positions=len(positions),
            effective_diversification=diversification_metrics['effective_diversification'],
            concentration_index=diversification_metrics['concentration_index'],
            correlation_average=diversification_metrics['correlation_average'],
            
            # Exposures
            sector_exposure=exposure_metrics['sector_exposure'],
            currency_exposure=exposure_metrics['currency_exposure'],
            issuer_exposure=exposure_metrics['issuer_exposure'],
            maturity_distribution=exposure_metrics['maturity_distribution'],
            
            # Performance attribution (semplificato)
            security_selection=0.0,  # Da implementare
            asset_allocation=0.0,    # Da implementare
            interaction_effect=0.0   # Da implementare
        )
        
        # Cache risultato
        self.analytics[portfolio_id] = metrics
        
        self.logger.info(f"Metriche portfolio {portfolio_id} calcolate: Market Value €{total_market_value:,.0f}")
        return metrics
    
    def get_portfolio_summary(self, portfolio_id: str) -> Dict[str, Any]:
        """Ottieni summary portafoglio"""
        
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} non trovato")
        
        config = self.portfolios[portfolio_id]
        positions = self.positions.get(portfolio_id, [])
        metrics = self.calculate_portfolio_metrics(portfolio_id)
        
        return {
            'config': config,
            'positions_count': len(positions),
            'positions': positions,
            'metrics': metrics,
            'last_updated': datetime.now(),
            'status': self._get_portfolio_status(portfolio_id, metrics)
        }
    
    # ========================================
    # PORTFOLIO OPTIMIZATION
    # ========================================
    
    def optimize_portfolio(self, portfolio_id: str, method: str = "mean_variance") -> Dict[str, float]:
        """Ottimizza allocazione portafoglio"""
        
        if portfolio_id not in self.positions:
            raise ValueError(f"Portfolio {portfolio_id} non trovato")
        
        positions = self.positions[portfolio_id]
        constraints = self.portfolios[portfolio_id].constraints
        
        self.logger.info(f"Ottimizzazione portfolio {portfolio_id} con metodo {method}")
        
        if method == "mean_variance":
            return self._optimize_mean_variance(positions, constraints)
        elif method == "risk_parity":
            return self._optimize_risk_parity(positions, constraints)
        elif method == "equal_weight":
            return self._optimize_equal_weight(positions, constraints)
        else:
            raise ValueError(f"Metodo ottimizzazione non supportato: {method}")
    
    def suggest_rebalancing(self, portfolio_id: str) -> Dict[str, Any]:
        """Suggerisce operazioni di ribilanciamento"""
        
        metrics = self.calculate_portfolio_metrics(portfolio_id)
        optimal_weights = self.optimize_portfolio(portfolio_id)
        positions = self.positions[portfolio_id]
        
        suggestions = []
        total_value = metrics.total_market_value
        
        for position in positions:
            current_weight = position.weight_current
            target_weight = optimal_weights.get(position.certificate_id, 0.0)
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > 0.02:  # Soglia 2%
                action = "BUY" if weight_diff > 0 else "SELL"
                amount = abs(weight_diff) * total_value
                
                suggestions.append({
                    'certificate_id': position.certificate_id,
                    'action': action,
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'weight_difference': weight_diff,
                    'amount': amount,
                    'priority': 'HIGH' if abs(weight_diff) > 0.05 else 'MEDIUM'
                })
        
        return {
            'portfolio_id': portfolio_id,
            'suggestions': suggestions,
            'total_rebalancing_amount': sum(s['amount'] for s in suggestions),
            'number_trades': len(suggestions),
            'optimization_benefit': self._calculate_optimization_benefit(portfolio_id, optimal_weights)
        }
    
    # ========================================
    # REPORTING & VISUALIZATION
    # ========================================
    
    def generate_portfolio_report(self, portfolio_id: str, output_path: Optional[str] = None) -> str:
        """Genera report Excel completo del portafoglio"""
        
        if output_path is None:
            output_path = str(self.base_dir)
        
        config = self.portfolios[portfolio_id]
        metrics = self.calculate_portfolio_metrics(portfolio_id)
        positions = self.positions[portfolio_id]
        
        # Nome file
        safe_name = config.name.replace(" ", "_")
        filename = f"Portfolio_Report_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = Path(output_path) / filename
        
        self.logger.info(f"Generazione report portfolio: {filepath}")
        
        # Usa EnhancedExcelExporter esistente
        try:
            # Crea workbook
            wb = self.excel_exporter._create_workbook()
            
            # Sheet 1: Portfolio Summary
            self._create_portfolio_summary_sheet(wb, config, metrics, positions)
            
            # Sheet 2: Positions Detail
            self._create_positions_detail_sheet(wb, positions)
            
            # Sheet 3: Risk Analysis
            self._create_portfolio_risk_sheet(wb, portfolio_id, metrics)
            
            # Sheet 4: Performance Analysis
            self._create_portfolio_performance_sheet(wb, portfolio_id, metrics)
            
            # Sheet 5: Optimization Suggestions
            suggestions = self.suggest_rebalancing(portfolio_id)
            self._create_optimization_sheet(wb, suggestions)
            
            # Salva
            wb.save(str(filepath))
            
            self.logger.info(f"Report portfolio salvato: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Errore generazione report: {e}")
            raise
    
    def create_portfolio_dashboard(self) -> pd.DataFrame:
        """Crea dashboard di tutti i portafogli con valori coerenti e robusti."""
        dashboard_data = []
        for portfolio_id, config in self.portfolios.items():
            try:
                # Calcola metriche, se possibile
                try:
                    metrics = self.calculate_portfolio_metrics(portfolio_id)
                    has_analysis = metrics and getattr(metrics, "total_market_value", 0) > 0
                except Exception:
                    metrics = None
                    has_analysis = False

                # Numero posizioni reale
                positions_count = len(self.positions.get(portfolio_id, []))

                # Ultima Analisi: solo se esiste e market value > 0
                ultima_analisi = "N/A"
                if has_analysis and hasattr(metrics, "timestamp"):
                    ultima_analisi = metrics.timestamp.strftime('%Y-%m-%d %H:%M')

                # Helper per formattare valori numerici o None
                def fmt(val, perc=False, euro=False):
                    if val is None:
                        return "N/A"
                    if isinstance(val, (int, float)):
                        if euro:
                            return f"€{val:,.0f}"
                        return f"{val:.2f}%" if perc else f"{val:.2f}"
                    return "N/A"

                row = {
                    'Portfolio ID': portfolio_id,
                    'Name': getattr(config, "name", ""),
                    'Type': getattr(config, "portfolio_type", "custom").value if hasattr(config, "portfolio_type") else str(getattr(config, "portfolio_type", "custom")),
                    'Positions': positions_count,
                    'Ultima Analisi': ultima_analisi,
                    'Market Value': fmt(getattr(metrics, "total_market_value", None), euro=True) if has_analysis else "N/A",
                    'Fair Value': fmt(getattr(metrics, "total_fair_value", None), euro=True) if has_analysis else "N/A",
                    'Total\nReturn': fmt(getattr(metrics, "total_return_pct", None), perc=True) if has_analysis else "N/A",
                    'FV\nGap': fmt(getattr(metrics, "fair_value_gap", None), perc=True) if has_analysis else "N/A",
                    'Volatility': fmt(getattr(metrics, "portfolio_volatility", None), perc=True) if has_analysis else "N/A",
                    'VaR\n95%': fmt(getattr(metrics, "portfolio_var_95", None), perc=True) if has_analysis else "N/A",
                    'Sharpe\nRatio': fmt(getattr(metrics, "sharpe_ratio", None)) if has_analysis else "N/A"
                }
                dashboard_data.append(row)
            except Exception as e:
                self.logger.warning(f"Errore dashboard per {portfolio_id}: {e}")
                row = {
                    'Portfolio ID': portfolio_id,
                    'Name': getattr(config, "name", ""),
                    'Type': getattr(config, "portfolio_type", "custom").value if hasattr(config, "portfolio_type") else str(getattr(config, "portfolio_type", "custom")),
                    'Positions': len(self.positions.get(portfolio_id, [])),
                    'Ultima Analisi': 'N/A',
                    'Market Value': 'N/A',
                    'Fair Value': 'N/A',
                    'Total\nReturn': 'N/A',
                    'FV\nGap': 'N/A',
                    'Volatility': 'N/A',
                    'VaR\n95%': 'N/A',
                    'Sharpe\nRatio': 'N/A'
                }
                dashboard_data.append(row)
        return pd.DataFrame(dashboard_data)
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _update_portfolio_weights(self, portfolio_id: str) -> None:
        """Aggiorna pesi correnti delle posizioni"""
        
        positions = self.positions[portfolio_id]
        total_value = sum(pos.market_value for pos in positions)
        
        if total_value > 0:
            for position in positions:
                position.weight_current = position.market_value / total_value
        else:
            for position in positions:
                position.weight_current = 0.0
    
    def _calculate_portfolio_risk(self, positions: List[PortfolioPosition]) -> Dict[str, float]:
        """Calcola metriche di rischio portfolio (semplificato)"""
        
        # Per ora implementazione semplificata
        # In futuro: Monte Carlo portfolio-level, correlazioni, etc.
        
        if not positions:
            return self._default_risk_metrics()
        
        # Weighted average delle metriche individuali
        total_weight = sum(pos.weight_current for pos in positions)
        
        if total_weight == 0:
            return self._default_risk_metrics()
        
        try:
            # Calcola risk metrics per ogni posizione
            individual_risks = []
            weights = []
            
            for position in positions:
                try:
                    analyzer = UnifiedCertificateAnalyzer(position.certificate)
                    risk_metrics = analyzer.calculate_risk_metrics(n_simulations=5000)
                    individual_risks.append(risk_metrics)
                    weights.append(position.weight_current)
                except Exception as e:
                    self.logger.warning(f"Risk calc failed for {position.certificate_id}: {e}")
                    # Usa valori default
                    individual_risks.append({
                        'volatility': 0.15,
                        'var_95': 0.10,
                        'expected_shortfall': 0.12,
                        'beta': 1.0,
                        'sharpe_ratio': 0.5
                    })
                    weights.append(position.weight_current)
            
            # Aggregate weighted metrics
            portfolio_volatility = sum(risk['volatility'] * w for risk, w in zip(individual_risks, weights))
            portfolio_var_95 = sum(risk['var_95'] * w for risk, w in zip(individual_risks, weights))
            portfolio_es = sum(risk['expected_shortfall'] * w for risk, w in zip(individual_risks, weights))
            portfolio_beta = sum(risk['beta'] * w for risk, w in zip(individual_risks, weights))
            portfolio_sharpe = sum(risk['sharpe_ratio'] * w for risk, w in zip(individual_risks, weights))
            
            return {
                'volatility': portfolio_volatility,
                'var_95': portfolio_var_95,
                'expected_shortfall': portfolio_es,
                'beta': portfolio_beta,
                'sharpe_ratio': portfolio_sharpe,
                'sortino_ratio': portfolio_sharpe * 1.1,  # Approx
                'max_drawdown': portfolio_var_95 * 1.5    # Approx
            }
            
        except Exception as e:
            self.logger.error(f"Errore calcolo portfolio risk: {e}")
            return self._default_risk_metrics()
    
    def _default_risk_metrics(self) -> Dict[str, float]:
        """Risk metrics di default"""
        return {
            'volatility': 0.12,
            'var_95': 0.08,
            'expected_shortfall': 0.10,
            'beta': 1.0,
            'sharpe_ratio': 0.5,
            'sortino_ratio': 0.6,
            'max_drawdown': 0.12
        }
    
    def _calculate_diversification_metrics(self, positions: List[PortfolioPosition]) -> Dict[str, float]:
        """Calcola metriche di diversificazione"""
        
        if not positions:
            return {
                'effective_diversification': 0.0,
                'concentration_index': 1.0,
                'correlation_average': 0.0
            }
        
        # Concentration Index (Herfindahl)
        weights = [pos.weight_current for pos in positions]
        concentration_index = sum(w**2 for w in weights)
        
        # Effective number of positions
        effective_diversification = 1 / concentration_index if concentration_index > 0 else len(positions)
        
        # Average correlation (semplificato)
        correlation_average = 0.3  # Da implementare con calcolo reale
        
        return {
            'effective_diversification': effective_diversification,
            'concentration_index': concentration_index,
            'correlation_average': correlation_average
        }
    
    def _calculate_exposure_metrics(self, positions: List[PortfolioPosition]) -> Dict[str, Any]:
        """Calcola metriche di esposizione"""
        
        sector_exposure = {}
        currency_exposure = {}
        issuer_exposure = {}
        maturity_distribution = {}
        
        for position in positions:
            weight = position.weight_current
            
            # Sector (semplificato - da certificate type)
            sector = position.certificate.specs.certificate_type
            sector_exposure[sector] = sector_exposure.get(sector, 0.0) + weight
            
            # Currency (da specs o default EUR)
            currency = getattr(position.certificate.specs, 'currency', 'EUR')
            currency_exposure[currency] = currency_exposure.get(currency, 0.0) + weight
            
            # Issuer (semplificato)
            issuer = getattr(position.certificate.specs, 'issuer', 'Unknown')
            issuer_exposure[issuer] = issuer_exposure.get(issuer, 0.0) + weight
            
            # Maturity bucket
            try:
                time_to_maturity = position.certificate.get_time_to_maturity()
                if time_to_maturity < 1:
                    bucket = "< 1Y"
                elif time_to_maturity < 3:
                    bucket = "1-3Y"
                elif time_to_maturity < 5:
                    bucket = "3-5Y"
                else:
                    bucket = "> 5Y"
                maturity_distribution[bucket] = maturity_distribution.get(bucket, 0.0) + weight
            except:
                maturity_distribution["Unknown"] = maturity_distribution.get("Unknown", 0.0) + weight
        
        return {
            'sector_exposure': sector_exposure,
            'currency_exposure': currency_exposure,
            'issuer_exposure': issuer_exposure,
            'maturity_distribution': maturity_distribution
        }
    
    def _empty_portfolio_metrics(self) -> PortfolioMetrics:
        """Metriche per portfolio vuoto"""
        return PortfolioMetrics(
            total_market_value=0.0,
            total_fair_value=0.0,
            total_nominal=0.0,
            total_pnl=0.0,
            total_return_pct=0.0,
            fair_value_gap=0.0,
            portfolio_volatility=0.0,
            portfolio_var_95=0.0,
            portfolio_expected_shortfall=0.0,
            portfolio_beta=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            number_positions=0,
            effective_diversification=0.0,
            concentration_index=0.0,
            correlation_average=0.0,
            sector_exposure={},
            currency_exposure={},
            issuer_exposure={},
            maturity_distribution={},
            security_selection=0.0,
            asset_allocation=0.0,
            interaction_effect=0.0
        )
    
    def _optimize_mean_variance(self, positions: List[PortfolioPosition], 
                               constraints: PortfolioConstraints) -> Dict[str, float]:
        """Ottimizzazione media-varianza (semplificata)"""
        
        # Implementazione semplificata - equal weight con vincoli
        n_positions = len(positions)
        if n_positions == 0:
            return {}
        
        # Equal weight come baseline
        equal_weight = 1.0 / n_positions
        max_weight = min(constraints.max_single_position, equal_weight * 2)
        
        weights = {}
        for position in positions:
            weights[position.certificate_id] = min(equal_weight, max_weight)
        
        # Normalizza a 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def _optimize_risk_parity(self, positions: List[PortfolioPosition],
                             constraints: PortfolioConstraints) -> Dict[str, float]:
        """Ottimizzazione risk parity (semplificata)"""
        
        # Per ora usa equal weight
        # In futuro: inverse volatility weighting
        return self._optimize_equal_weight(positions, constraints)
    
    def _optimize_equal_weight(self, positions: List[PortfolioPosition],
                              constraints: PortfolioConstraints) -> Dict[str, float]:
        """Ottimizzazione equal weight"""
        
        n_positions = len(positions)
        if n_positions == 0:
            return {}
        
        weight = 1.0 / n_positions
        max_weight = constraints.max_single_position
        
        # Applica vincolo max position
        actual_weight = min(weight, max_weight)
        
        weights = {}
        for position in positions:
            weights[position.certificate_id] = actual_weight
        
        return weights
    
    def _calculate_optimization_benefit(self, portfolio_id: str, 
                                      optimal_weights: Dict[str, float]) -> float:
        """Calcola beneficio dell'ottimizzazione (semplificato)"""
        
        # Per ora ritorna valore fisso
        # In futuro: calcolo expected utility improvement
        return 0.05  # 5% improvement estimate
    
    def _get_portfolio_status(self, portfolio_id: str, metrics: PortfolioMetrics) -> str:
        """Determina status del portafoglio"""
        
        constraints = self.portfolios[portfolio_id].constraints
        
        # Check vincoli principali
        if metrics.number_positions < constraints.min_diversification:
            return "UNDER_DIVERSIFIED"
        elif metrics.portfolio_volatility > constraints.max_volatility:
            return "HIGH_RISK"
        elif metrics.portfolio_var_95 > constraints.max_var_95:
            return "VAR_BREACH"
        elif metrics.concentration_index > 0.5:
            return "CONCENTRATED"
        elif abs(metrics.fair_value_gap) > 0.1:
            return "MISPRICED"
        else:
            return "HEALTHY"
    
    # ========================================
    # EXCEL REPORTING HELPERS
    # ========================================
    
    def _create_portfolio_summary_sheet(self, wb, config: PortfolioConfig, 
                                       metrics: PortfolioMetrics, 
                                       positions: List[PortfolioPosition]) -> None:
        """Crea sheet summary portfolio"""
        
        ws = wb.create_sheet("Portfolio Summary")
        
        # Headers e dati di base
        ws['A1'] = "PORTFOLIO SUMMARY"
        ws['A3'] = "Portfolio Name:"
        ws['B3'] = config.name
        ws['A4'] = "Portfolio Type:"
        ws['B4'] = config.portfolio_type.value
        ws['A5'] = "Inception Date:"
        ws['B5'] = config.inception_date.strftime('%Y-%m-%d')
        ws['A6'] = "Base Currency:"
        ws['B6'] = config.base_currency
        ws['A7'] = "Number of Positions:"
        ws['B7'] = len(positions)
        
        # Metriche finanziarie
        ws['A9'] = "FINANCIAL METRICS"
        ws['A11'] = "Total Market Value:"
        ws['B11'] = f"€{metrics.total_market_value:,.0f}"
        ws['A12'] = "Total Fair Value:"
        ws['B12'] = f"€{metrics.total_fair_value:,.0f}"
        ws['A13'] = "Total P&L:"
        ws['B13'] = f"€{metrics.total_pnl:,.0f}"
        ws['A14'] = "Total Return:"
        ws['B14'] = f"{metrics.total_return_pct:.2%}"
        ws['A15'] = "Fair Value Gap:"
        ws['B15'] = f"{metrics.fair_value_gap:.2%}"
        
        # Risk metrics
        ws['A17'] = "RISK METRICS"
        ws['A19'] = "Portfolio Volatility:"
        ws['B19'] = f"{metrics.portfolio_volatility:.2%}"
        ws['A20'] = "VaR 95%:"
        ws['B20'] = f"{metrics.portfolio_var_95:.2%}"
        ws['A21'] = "Expected Shortfall:"
        ws['B21'] = f"{metrics.portfolio_expected_shortfall:.2%}"
        ws['A22'] = "Sharpe Ratio:"
        ws['B22'] = f"{metrics.sharpe_ratio:.2f}"
        ws['A23'] = "Beta:"
        ws['B23'] = f"{metrics.portfolio_beta:.2f}"
    
    def _create_positions_detail_sheet(self, wb, positions: List[PortfolioPosition]) -> None:
        """Crea sheet dettaglio posizioni"""
        
        ws = wb.create_sheet("Positions Detail")
        
        # Headers
        headers = [
            "Certificate ID", "Name", "Type", "Nominal Amount", "Market Value",
            "Fair Value", "Entry Price", "Current Price", "Weight %", 
            "Unrealized P&L", "Return %", "Entry Date"
        ]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # Data
        for row, position in enumerate(positions, 2):
            ws.cell(row=row, column=1, value=position.certificate_id)
            ws.cell(row=row, column=2, value=position.certificate.specs.name)
            ws.cell(row=row, column=3, value=position.certificate.specs.certificate_type)
            ws.cell(row=row, column=4, value=position.nominal_amount)
            ws.cell(row=row, column=5, value=position.market_value)
            ws.cell(row=row, column=6, value=position.fair_value)
            ws.cell(row=row, column=7, value=position.entry_price)
            ws.cell(row=row, column=8, value=position.current_price)
            ws.cell(row=row, column=9, value=f"{position.weight_current:.2%}")
            ws.cell(row=row, column=10, value=position.unrealized_pnl)
            ws.cell(row=row, column=11, value=f"{(position.current_price/position.entry_price - 1):.2%}")
            ws.cell(row=row, column=12, value=position.entry_date.strftime('%Y-%m-%d'))
    
    def _create_portfolio_risk_sheet(self, wb, portfolio_id: str, metrics: PortfolioMetrics) -> None:
        """Crea sheet analisi rischio portfolio"""
        
        ws = wb.create_sheet("Risk Analysis")
        
        ws['A1'] = "PORTFOLIO RISK ANALYSIS"
        
        # Risk metrics summary
        ws['A3'] = "Risk Metrics Summary"
        risk_data = [
            ["Metric", "Value", "Status"],
            ["Portfolio Volatility", f"{metrics.portfolio_volatility:.2%}", "OK" if metrics.portfolio_volatility < 0.20 else "HIGH"],
            ["VaR 95%", f"{metrics.portfolio_var_95:.2%}", "OK" if metrics.portfolio_var_95 < 0.10 else "HIGH"],
            ["Expected Shortfall", f"{metrics.portfolio_expected_shortfall:.2%}", "OK" if metrics.portfolio_expected_shortfall < 0.12 else "HIGH"],
            ["Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}", "OK" if metrics.sharpe_ratio > 0.5 else "LOW"],
            ["Concentration Index", f"{metrics.concentration_index:.2f}", "OK" if metrics.concentration_index < 0.3 else "HIGH"]
        ]
        
        for row, data in enumerate(risk_data, 5):
            for col, value in enumerate(data, 1):
                ws.cell(row=row, column=col, value=value)
    
    def _create_portfolio_performance_sheet(self, wb, portfolio_id: str, metrics: PortfolioMetrics) -> None:
        """Crea sheet performance analysis"""
        
        ws = wb.create_sheet("Performance Analysis")
        
        ws['A1'] = "PORTFOLIO PERFORMANCE ANALYSIS"
        
        # Performance summary
        ws['A3'] = "Performance Summary"
        perf_data = [
            ["Metric", "Value"],
            ["Total Return", f"{metrics.total_return_pct:.2%}"],
            ["Fair Value Gap", f"{metrics.fair_value_gap:.2%}"],
            ["Number of Positions", str(metrics.number_positions)],
            ["Effective Diversification", f"{metrics.effective_diversification:.1f}"],
            ["Average Correlation", f"{metrics.correlation_average:.2f}"]
        ]
        
        for row, data in enumerate(perf_data, 5):
            for col, value in enumerate(data, 1):
                ws.cell(row=row, column=col, value=value)
    
    def _create_optimization_sheet(self, wb, suggestions: Dict[str, Any]) -> None:
        """Crea sheet suggerimenti ottimizzazione"""
        
        ws = wb.create_sheet("Optimization")
        
        ws['A1'] = "PORTFOLIO OPTIMIZATION SUGGESTIONS"
        
        if not suggestions['suggestions']:
            ws['A3'] = "No rebalancing suggestions - portfolio is well balanced"
            return
        
        # Headers
        headers = ["Certificate ID", "Action", "Current Weight", "Target Weight", "Difference", "Amount", "Priority"]
        for col, header in enumerate(headers, 1):
            ws.cell(row=3, column=col, value=header)
        
        # Suggestions
        for row, suggestion in enumerate(suggestions['suggestions'], 4):
            ws.cell(row=row, column=1, value=suggestion['certificate_id'])
            ws.cell(row=row, column=2, value=suggestion['action'])
            ws.cell(row=row, column=3, value=f"{suggestion['current_weight']:.2%}")
            ws.cell(row=row, column=4, value=f"{suggestion['target_weight']:.2%}")
            ws.cell(row=row, column=5, value=f"{suggestion['weight_difference']:.2%}")
            ws.cell(row=row, column=6, value=f"€{suggestion['amount']:,.0f}")
            ws.cell(row=row, column=7, value=suggestion['priority'])
    
    # ========================================
    # PERSISTENCE
    # ========================================
    
    def _load_portfolios(self) -> None:
        """Carica portafogli da file"""
        if not self.portfolios_file.exists():
            self.logger.info("File portfolios non esistente, inizializzazione vuota")
            self.portfolios = {}
            return
        try:
            with open(self.portfolios_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for portfolio_id, config_data in data.items():
                config = self._deserialize_portfolio_config(config_data)
                self.portfolios[portfolio_id] = config
            self.logger.info(f"Caricati {len(self.portfolios)} portafogli")
        except Exception as e:
            self.logger.error(f"Errore caricamento portfolios: {e}")

    def _save_portfolios(self) -> None:
        """Salva portafogli su file"""
        try:
            data = {}
            for portfolio_id, config in self.portfolios.items():
                data[portfolio_id] = self._serialize_portfolio_config(config)
            with open(self.portfolios_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            self.logger.info(f"Salvati {len(self.portfolios)} portafogli")
        except Exception as e:
            self.logger.error(f"Errore salvataggio portfolios: {e}")

    def _load_positions(self) -> None:
        """Carica posizioni da file"""
        if not self.positions_file.exists():
            self.logger.info("File positions non esistente, inizializzazione vuota")
            self.positions = {}
            return
        try:
            with open(self.positions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for portfolio_id, positions_data in data.items():
                # Carica come lista di dict (basta per il conteggio)
                self.positions[portfolio_id] = positions_data
            self.logger.info(f"Caricati positions per {len(self.positions)} portafogli")
        except Exception as e:
            self.logger.error(f"Errore caricamento positions: {e}")

    def _save_positions(self) -> None:
        """Salva posizioni su file"""
        try:
            data = {}
            for portfolio_id, positions in self.positions.items():
                data[portfolio_id] = [
                    {
                        'certificate_id': pos.certificate_id,
                        'nominal_amount': pos.nominal_amount,
                        'entry_price': pos.entry_price,
                        'entry_date': pos.entry_date.isoformat(),
                        # Altri campi da aggiungere
                    }
                    for pos in positions
                ]
            with open(self.positions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            self.logger.info(f"Salvate positions per {len(self.positions)} portafogli")
        except Exception as e:
            self.logger.error(f"Errore salvataggio positions: {e}")

    def _serialize_portfolio_config(self, config: PortfolioConfig) -> Dict[str, Any]:
        """Serializza PortfolioConfig per JSON"""
        return {
            'name': config.name,
            'description': config.description,
            'portfolio_type': config.portfolio_type.value,
            'base_currency': config.base_currency,
            'inception_date': config.inception_date.isoformat(),
            'target_size': config.target_size,
            'constraints': {
                'max_single_position': config.constraints.max_single_position,
                'max_issuer_exposure': config.constraints.max_issuer_exposure,
                'max_sector_exposure': config.constraints.max_sector_exposure,
                'max_currency_exposure': config.constraints.max_currency_exposure,
                'min_diversification': config.constraints.min_diversification,
                'max_correlation': config.constraints.max_correlation,
                'min_duration': config.constraints.min_duration,
                'max_duration': config.constraints.max_duration,
                'target_return': config.constraints.target_return,
                'max_volatility': config.constraints.max_volatility,
                'max_var_95': config.constraints.max_var_95
            },
            'rebalancing_frequency': config.rebalancing_frequency.value,
            'auto_rebalancing': config.auto_rebalancing,
            'benchmark': config.benchmark,
            'manager': config.manager,
            'risk_profile': config.risk_profile
        }
    
    def _deserialize_portfolio_config(self, data: Dict[str, Any]) -> PortfolioConfig:
        """Deserializza PortfolioConfig da JSON"""
        
        constraints = PortfolioConstraints(
            max_single_position=data['constraints']['max_single_position'],
            max_issuer_exposure=data['constraints']['max_issuer_exposure'],
            max_sector_exposure=data['constraints']['max_sector_exposure'],
            max_currency_exposure=data['constraints']['max_currency_exposure'],
            min_diversification=data['constraints']['min_diversification'],
            max_correlation=data['constraints']['max_correlation'],
            min_duration=data['constraints']['min_duration'],
            max_duration=data['constraints']['max_duration'],
            target_return=data['constraints']['target_return'],
            max_volatility=data['constraints']['max_volatility'],
            max_var_95=data['constraints']['max_var_95']
        )
        
        return PortfolioConfig(
            name=data['name'],
            description=data['description'],
            portfolio_type=PortfolioType(data['portfolio_type']),
            base_currency=data['base_currency'],
            inception_date=datetime.fromisoformat(data['inception_date']),
            target_size=data['target_size'],
            constraints=constraints,
            rebalancing_frequency=RebalancingFrequency(data['rebalancing_frequency']),
            auto_rebalancing=data['auto_rebalancing'],
            benchmark=data.get('benchmark'),
            manager=data['manager'],
            risk_profile=data['risk_profile']
        )

# ========================================
# PORTFOLIO GUI INTEGRATION
# ========================================

class PortfolioGUIManager:
    """Manager GUI per portafogli - integrazione con fixed_gui_manager"""
    
    def __init__(self, portfolio_manager: PortfolioManager, root_window=None, certificates_data=None, enhanced_manager=None):
        self.portfolio_manager = portfolio_manager
        self.logger = logging.getLogger(f"{__name__}.PortfolioGUIManager")
        self.root_window = root_window
        self.certificates_data = certificates_data
        self.enhanced_manager = enhanced_manager  # Passa EnhancedCertificateManagerV15 qui
    
    def create_portfolio_creation_dialog(self) -> Optional[str]:
        """Crea dialog per creazione nuovo portafoglio"""
        
        # Implementazione GUI dialog
        # Per ora ritorna esempio
        
        example_config = PortfolioConfig(
            name="Conservative Income Portfolio",
            description="Portfolio conservativo focalizzato su reddito",
            portfolio_type=PortfolioType.CONSERVATIVE,
            base_currency="EUR",
            target_size=500000.0,
            constraints=PortfolioConstraints(
                max_single_position=0.15,
                max_issuer_exposure=0.25,
                target_return=0.06,
                max_volatility=0.12
            )
        )
        
        portfolio_id = self.portfolio_manager.create_portfolio(example_config)
        return portfolio_id
    
    def create_portfolio_dashboard_window(self):
        """Crea finestra dashboard portafogli"""
        
        # 1. Ottieni i dati per la dashboard
        dashboard_df = self.portfolio_manager.create_portfolio_dashboard()
        
       # 2. Crea la  finestra Toplevel (la finestra del portfoglio)
        dashboard_window = tk.Toplevel(self.root_window)
        dashboard_window.title("📁 Portfolio Management Dashboard")
        dashboard_window.geometry("1200x800") # Set a default size
        dashboard_window.transient(self.root_window) # Keep on top of root
        dashboard_window.grab_set() # Modal-like behavior

        # Main frame for the window
        main_frame = ttk.Frame(dashboard_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Portfolio Overview", font=("Arial", 16, "bold")).pack(pady=(0, 10))

        # Frame for the Treeview and scrollbar
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview to display the DataFrame
        columns = [
            "Portfolio ID", "Name", "Type", "Positions", "Ultima Analisi",
            "Market Value", "Fair Value", "Total\nReturn", "FV\nGap",
            "Volatility", "VaR\n95%", "Sharpe\nRatio"
        ]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        col_widths = {
            "Portfolio ID": 140,
            "Name": 160,
            "Type": 90,
            "Positions": 80,
            "Ultima Analisi": 110,
            "Market Value": 110,
            "Fair Value": 110,
            "Total\nReturn": 70,
            "FV\nGap": 70,
            "Volatility": 70,
            "VaR\n95%": 70,
            "Sharpe\nRatio": 80
        }
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor="center")
        # Migliora la leggibilità delle intestazioni (padding verticale)
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), padding=[0, 10])

        # Add data to the Treeview
        for index, row in dashboard_df.iterrows():
            self.tree.insert("", tk.END, values=list(row))

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack the Treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Inizio Sezione Pulsanti Riorganizzata ---
        button_bar_frame = ttk.Frame(main_frame)
        button_bar_frame.pack(fill=tk.X, pady=(10, 0))

        # Pulsanti operativi raggruppati a sinistra
        actions_group_frame = ttk.Frame(button_bar_frame)
        actions_group_frame.pack(side=tk.LEFT)

        ttk.Button(actions_group_frame, text="➕ Nuovo Portfolio",
                   command=self._create_new_portfolio_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_group_frame, text="✏️ Modifica Selezionato",
                   command=self._edit_selected_portfolio).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_group_frame, text="🗑️ Elimina Selezionato",
                   command=self._delete_selected_portfolio).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_group_frame, text="📊 Analizza Selezionato",
                   command=self._analyze_selected_portfolio).pack(side=tk.LEFT, padx=(0, 5))

        # Pulsante Chiudi Dashboard a destra
        ttk.Button(button_bar_frame, text="🚪 Chiudi Dashboard",
                   command=dashboard_window.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        # --- Fine Sezione Pulsanti Riorganizzata ---
            
        # Memorizza il riferimento al treeview per interazioni future
        self.portfolio_tree = self.tree
        self.portfolio_tree.bind("<<TreeviewSelect>>", self._on_portfolio_selected_in_dashboard)


        # Make the window visible and wait for it to close
        dashboard_window.wait_window()

    # Add a method to update certificates data if needed by the GUI Manager
    def update_certificates_data(self, certificates_data):
        """Updates the certificates data stored in the GUI Manager."""
        self.certificates_data = certificates_data
        self.logger.info(f"Certificates data updated in PortfolioGUIManager ({len(certificates_data)} certs)")

    # Add placeholder methods for portfolio actions
#    def create_portfolio_dialog(self):
#        """Placeholder for creating a new portfolio dialog."""
#        messagebox.showinfo("Portfolio Action", "Create New Portfolio functionality here.")


    def _create_new_portfolio_dialog(self):
        """Dialog per creazione nuovo portafoglio con selezione strumenti e tipo."""
        dialog = tk.Toplevel(self.root_window)
        dialog.title("Nuovo Portfolio")
        dialog.geometry("700x700")
        dialog.transient(self.root_window)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Nome portfolio
        ttk.Label(main_frame, text="Nome Portfolio:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 2))
        nome_var = tk.StringVar()
        nome_entry = ttk.Entry(main_frame, textvariable=nome_var, width=40)
        nome_entry.pack(fill=tk.X, pady=(0, 10))

        # Tipo portafoglio
        ttk.Label(main_frame, text="Tipo di Portafoglio:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 2))
        tipo_var = tk.StringVar(value="custom")
        tipi = [e.value for e in PortfolioType]
        tipo_combo = ttk.Combobox(main_frame, values=tipi, textvariable=tipo_var, state="readonly", width=30)
        tipo_combo.pack(anchor=tk.W, pady=(0, 2))

        # Descrizione tipo portafoglio
        tipo_descrizioni = {
            "conservative": "Basso rischio, alta liquidità, protezione capitale.",
            "balanced": "Equilibrio tra rischio e rendimento, diversificazione ampia.",
            "aggressive": "Alto rischio, focus su crescita e rendimento.",
            "income_focused": "Obiettivo principale: generare reddito periodico.",
            "capital_protection": "Massima protezione del capitale investito.",
            "growth": "Focus su crescita del capitale nel lungo periodo.",
            "income": "Portafoglio orientato a flussi cedolari.",
            "absolute_return": "Obiettivo: rendimento positivo indipendente dal mercato.",
            "custom": "Configurazione personalizzata dall’utente."
        }
        tipo_descr_label = ttk.Label(main_frame, text=tipo_descrizioni.get(tipo_var.get(), ""), font=("Arial", 9, "italic"), foreground="gray", wraplength=600)
        tipo_descr_label.pack(anchor=tk.W, pady=(0, 10))

        def update_descr(*args):
            tipo_descr_label.config(text=tipo_descrizioni.get(tipo_var.get(), ""))
        tipo_combo.bind("<<ComboboxSelected>>", update_descr)
        update_descr()

        # Note descrittive
        ttk.Label(main_frame, text="Note descrittive:", font=("Arial", 11)).pack(anchor=tk.W)
        note_text = tk.Text(main_frame, height=3, width=60, wrap=tk.WORD)
        note_text.pack(fill=tk.X, pady=(0, 10))

        # Filtro tipologia strumento
        ttk.Label(main_frame, text="Filtra per tipologia:", font=("Arial", 11)).pack(anchor=tk.W)
        filter_var = tk.StringVar(value="Tutti")
        tipi_cert = ["Tutti"]
        if self.certificates_data:
            tipi_cert += sorted(set(c.get('certificate_type', 'N/A') for c in self.certificates_data.values()))
        filter_combo = ttk.Combobox(main_frame, values=tipi_cert, textvariable=filter_var, state="readonly", width=20)
        filter_combo.pack(anchor=tk.W, pady=(0, 5))

        # Lista strumenti disponibili (multiselezione)
        ttk.Label(main_frame, text="Seleziona strumenti da includere:", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        listbox = tk.Listbox(main_frame, selectmode=tk.MULTIPLE, width=80, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        def update_listbox(*args):
            listbox.delete(0, tk.END)
            if not self.certificates_data:
                return
            selected_type = filter_var.get()
            for isin, cert in self.certificates_data.items():
                tipo = cert.get('certificate_type', 'N/A')
                if selected_type == "Tutti" or tipo == selected_type:
                    display = f"{isin} | {cert.get('name', '')} | {tipo}"
                    listbox.insert(tk.END, display)
        filter_combo.bind("<<ComboboxSelected>>", update_listbox)
        update_listbox()

        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        def on_save():
            nome = nome_var.get().strip()
            note = note_text.get("1.0", tk.END).strip()
            selected_indices = listbox.curselection()
            tipo_sel = tipo_var.get()
            if not nome:
                messagebox.showerror("Errore", "Il nome del portfolio è obbligatorio.", parent=dialog)
                nome_entry.focus()
                return
            if len(selected_indices) < 2:
                messagebox.showwarning("Attenzione", "Devi selezionare almeno 2 strumenti finanziari per creare un portfolio.", parent=dialog)
                return
            # Ottieni gli ISIN selezionati
            selected_isins = []
            for idx in selected_indices:
                display = listbox.get(idx)
                isin = display.split('|')[0].strip()
                selected_isins.append(isin)
            # Crea PortfolioConfig con tipo scelto
            config = PortfolioConfig(
                name=nome,
                description=note,
                portfolio_type=PortfolioType(tipo_sel)
            )
            portfolio_id = self.portfolio_manager.create_portfolio(config)
            for isin in selected_isins:
                cert = self.certificates_data.get(isin)
                if cert:
                    self.portfolio_manager.add_position(
                        portfolio_id=portfolio_id,
                        certificate_id=isin,
                        certificate=None,
                        nominal_amount=1000.0,
                        entry_price=100.0
                    )
            messagebox.showinfo("Successo", f"Portfolio '{nome}' creato con {len(selected_isins)} strumenti.", parent=dialog)
            dialog.destroy()
            self._refresh_portfolio_dashboard()

        def on_cancel():
            dialog.destroy()

        ttk.Button(button_frame, text="Salva Portfolio", command=on_save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Annulla", command=on_cancel).pack(side=tk.RIGHT)

        nome_entry.focus()

    def _refresh_portfolio_dashboard(self):
        """Aggiorna la dashboard dopo inserimento/eliminazione portafogli."""
        dashboard_df = self.portfolio_manager.create_portfolio_dashboard()
        self.portfolio_tree.delete(*self.portfolio_tree.get_children())
        for index, row in dashboard_df.iterrows():
            self.portfolio_tree.insert("", tk.END, values=list(row))

    def _edit_selected_portfolio(self):
        """Modifica il portfolio selezionato: denominazione, tipo, note, composizione."""
        selected_item = self.portfolio_tree.selection()
        if not selected_item:
            messagebox.showwarning("Attenzione", "Seleziona un portfolio da modificare.")
            return
        portfolio_id = self.portfolio_tree.item(selected_item[0])['values'][0]
        config = self.portfolio_manager.portfolios.get(portfolio_id)
        if not config:
            messagebox.showerror("Errore", "Portfolio non trovato.")
            return

        # Recupera dati attuali
        nome_attuale = getattr(config, "name", "")
        tipo_attuale = getattr(config, "portfolio_type", "custom")
        note_attuali = getattr(config, "description", "")
        composizione_attuale = [pos['certificate_id'] if isinstance(pos, dict) else pos.certificate_id
                                for pos in self.portfolio_manager.positions.get(portfolio_id, [])]

        # --- Dialog di modifica ---
        dialog = tk.Toplevel(self.root_window)
        dialog.title(f"Modifica Portfolio: {nome_attuale}")
        dialog.geometry("700x600")
        dialog.transient(self.root_window)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Denominazione
        ttk.Label(main_frame, text="Denominazione:", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        nome_var = tk.StringVar(value=nome_attuale)
        ttk.Entry(main_frame, textvariable=nome_var, width=40).pack(fill=tk.X, pady=(0, 10))

        # Tipo portafoglio + descrizione dinamica
        ttk.Label(main_frame, text="Tipo di Portafoglio:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 2))
        tipo_var = tk.StringVar(value=tipo_attuale.value if hasattr(tipo_attuale, "value") else str(tipo_attuale))
        tipi = [e.value for e in PortfolioType]
        tipo_combo = ttk.Combobox(main_frame, values=tipi, textvariable=tipo_var, state="readonly", width=30)
        tipo_combo.pack(anchor=tk.W, pady=(0, 2))

        # Descrizione dinamica tipo portafoglio
        tipo_descrizioni = {
            "conservative": "Basso rischio, alta liquidità, protezione capitale.",
            "balanced": "Equilibrio tra rischio e rendimento, diversificazione ampia.",
            "aggressive": "Alto rischio, focus su crescita e rendimento.",
            "income_focused": "Obiettivo principale: generare reddito periodico.",
            "capital_protection": "Massima protezione del capitale investito.",
            "growth": "Focus su crescita del capitale nel lungo periodo.",
            "income": "Portafoglio orientato a flussi cedolari.",
            "absolute_return": "Obiettivo: rendimento positivo indipendente dal mercato.",
            "custom": "Configurazione personalizzata dall’utente."
        }
        tipo_descr_label = ttk.Label(main_frame, text=tipo_descrizioni.get(tipo_var.get(), ""), font=("Arial", 9, "italic"), foreground="gray", wraplength=600)
        tipo_descr_label.pack(anchor=tk.W, pady=(0, 10))

        def update_descr(*args):
            tipo_descr_label.config(text=tipo_descrizioni.get(tipo_var.get(), ""))
        tipo_combo.bind("<<ComboboxSelected>>", update_descr)
        update_descr()

        # Note
        ttk.Label(main_frame, text="Note:", font=("Arial", 11)).pack(anchor=tk.W)
        note_text = tk.Text(main_frame, height=3, width=60, wrap=tk.WORD)
        note_text.insert("1.0", note_attuali)
        note_text.pack(fill=tk.X, pady=(0, 10))

        # Composizione (multiselezione) - mostra sempre tutti i certificati disponibili
        ttk.Label(main_frame, text="Composizione (ISIN):", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        listbox = tk.Listbox(main_frame, selectmode=tk.MULTIPLE, width=80, height=12)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        all_isins = []
        if self.certificates_data:
            # Supporta sia dict che lista di certificati
            certs = self.certificates_data.items() if isinstance(self.certificates_data, dict) else [(c.get('isin', ''), c) for c in self.certificates_data]
            for isin, cert in certs:
                display = f"{isin} | {cert.get('name', '')} | {cert.get('certificate_type', '')}"
                listbox.insert(tk.END, display)
                all_isins.append(isin)
        # Seleziona quelli già presenti
        for idx, isin in enumerate(all_isins):
            if isin in composizione_attuale:
                listbox.selection_set(idx)

        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def on_save():
            nuovo_nome = nome_var.get().strip()
            nuovo_tipo = tipo_var.get()
            nuove_note = note_text.get("1.0", tk.END).strip()
            selected_indices = listbox.curselection()
            nuova_composizione = [all_isins[idx] for idx in selected_indices]

            if not nuovo_nome:
                messagebox.showerror("Errore", "Il nome del portfolio è obbligatorio.", parent=dialog)
                return
            if len(nuova_composizione) < 2:
                messagebox.showwarning("Attenzione", "Devi selezionare almeno 2 strumenti finanziari.", parent=dialog)
                return

            composizione_modificata = set(nuova_composizione) != set(composizione_attuale)
            metrics = self.portfolio_manager.analytics.get(portfolio_id)
            analisi_presenti = metrics and getattr(metrics, "total_market_value", 0) > 0

            if composizione_modificata and analisi_presenti:
                if not messagebox.askyesno(
                    "Attenzione: Modifica Distruttiva",
                    "Modificando la composizione perderai TUTTI i dati di analisi associati a questo portafoglio.\n"
                    "Questa operazione è IRREVERSIBILE.\nProcedere?",
                    parent=dialog
                ):
                    return
                self.portfolio_manager.analytics[portfolio_id] = None

            config.name = nuovo_nome
            config.portfolio_type = PortfolioType(nuovo_tipo)
            config.description = nuove_note

            if composizione_modificata:
                new_positions = []
                for isin in nuova_composizione:
                    cert = None
                    if self.certificates_data:
                        if isinstance(self.certificates_data, dict):
                            cert = self.certificates_data.get(isin)
                        else:
                            for c in self.certificates_data:
                                if c.get('isin', '') == isin:
                                    cert = c
                                    break
                    pos = {
                        'certificate_id': isin,
                        'nominal_amount': 1000.0,
                        'entry_price': 100.0,
                        'entry_date': datetime.now().isoformat()
                    }
                    new_positions.append(pos)
                self.portfolio_manager.positions[portfolio_id] = new_positions

            self.portfolio_manager._save_portfolios()
            self.portfolio_manager._save_positions()
            self._refresh_portfolio_dashboard()
            dialog.destroy()
            messagebox.showinfo("Modifica completata", "Portafoglio modificato con successo.")

        def on_cancel():
            dialog.destroy()

        ttk.Button(button_frame, text="Salva", command=on_save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Annulla", command=on_cancel).pack(side=tk.RIGHT)

        dialog.focus_set()

    def _delete_selected_portfolio(self):
        """Elimina realmente il portfolio selezionato dalla dashboard."""
        selected_item = self.portfolio_tree.selection()
        if not selected_item:
            messagebox.showwarning("Attenzione", "Seleziona un portfolio da eliminare.")
            return
        portfolio_id = self.portfolio_tree.item(selected_item[0])['values'][0]
        nome_portfolio = self.portfolio_tree.item(selected_item[0])['values'][1]
        if not messagebox.askyesno("Conferma Eliminazione",
                                   f"Eliminare definitivamente il portfolio '{nome_portfolio}' ({portfolio_id})?\nL'operazione non è reversibile."):
            return

        try:
            # Rimuovi dal manager
            if portfolio_id in self.portfolio_manager.portfolios:
                del self.portfolio_manager.portfolios[portfolio_id]
            if portfolio_id in self.portfolio_manager.positions:
                del self.portfolio_manager.positions[portfolio_id]
            if portfolio_id in self.portfolio_manager.analytics:
                del self.portfolio_manager.analytics[portfolio_id]
            self.portfolio_manager._save_portfolios()
            self.portfolio_manager._save_positions()
            # Aggiorna la dashboard (Treeview)
            self.portfolio_tree.delete(selected_item[0])
            messagebox.showinfo("Eliminato", f"Portfolio '{nome_portfolio}' eliminato con successo.")
            self.logger.info(f"Portfolio '{portfolio_id}' eliminato.")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'eliminazione del portfolio:\n{e}")
            self.logger.error(f"Errore eliminazione portfolio {portfolio_id}: {e}")

    def _analyze_selected_portfolio(self):
        """Analizza il certificato selezionato nel portafoglio tramite EnhancedCertificateManager."""
        selected_item = self.portfolio_tree.selection()
        if not selected_item:
            messagebox.showwarning("Attenzione", "Seleziona un portfolio da analizzare.")
            return
        portfolio_id = self.portfolio_tree.item(selected_item[0])['values'][0]
        positions = self.portfolio_manager.positions.get(portfolio_id, [])
        if not positions:
            messagebox.showinfo("Analisi Portfolio", "Nessun certificato presente nel portafoglio selezionato.")
            return
        cert_id = positions[0]['certificate_id'] if isinstance(positions[0], dict) else positions[0].certificate_id

        enhanced_config = self.enhanced_manager.configurations.get(cert_id)
        if not enhanced_config:
            messagebox.showerror("Errore", f"Certificato {cert_id} non trovato nell'archivio avanzato.")
            return

        stato = getattr(enhanced_config, 'status', 'unknown')
        stato_descr = {
            "new": "Nuovo (mai valutato, nessun evento)",
            "in_life": "In corso (in-life)",
            "matured": "Scaduto (maturity raggiunta)",
            "autocalled": "Autocall anticipato"
        }.get(stato, stato)

        info = f"ISIN: {cert_id}\nNome: {getattr(enhanced_config.base_config, 'name', '')}\nTipo: {getattr(enhanced_config.base_config, 'certificate_type', '')}\n"
        info += f"Stato: {stato_descr}\n"
        info += f"Valuation Date: {enhanced_config.in_life_state.valuation_date.strftime('%Y-%m-%d')}\n"
        info += f"Memory Coupons: {len(enhanced_config.in_life_state.memory_coupons_due)}\n"
        info += f"Ultimo prezzo spot: {getattr(enhanced_config.base_config, 'current_spots', None)}"
        messagebox.showinfo("Analisi Certificato", info)

    def _on_portfolio_selected_in_dashboard(self, event=None):
        """Gestisce la selezione di un portfolio nella tabella del dashboard."""
        selected_item = self.portfolio_tree.selection()
        if selected_item:
            portfolio_id = self.portfolio_tree.item(selected_item[0])['values'][0]
            self.logger.info(f"Portfolio '{portfolio_id}' selezionato nel dashboard.")
            # Qui puoi aggiungere logica per abilitare/disabilitare pulsanti o mostrare dettagli
        if selected_item:
            portfolio_id = self.portfolio_tree.item(selected_item[0])['values'][0]
            self.logger.info(f"Portfolio '{portfolio_id}' selezionato nel dashboard.")
            # Qui puoi aggiungere logica per abilitare/disabilitare pulsanti o mostrare dettagli
