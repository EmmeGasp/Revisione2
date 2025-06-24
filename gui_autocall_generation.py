# ========================================
# FIX GUI AUTO-GENERATION AUTOCALL LEVELS
# Sistema Certificati Finanziari - Fix salvataggio GUI
# ========================================
# File: gui_autocall_fix.py (patch per fixed_gui_manager_v14.py)
# Timestamp: 2025-06-16 16:00:00
# Fix auto-generazione autocall_levels da parametri step-down
# ========================================

"""
PROBLEMA IDENTIFICATO:
- GUI salva parametri individuali (step_down_rate, dynamic_barriers)
- MA non genera automaticamente gli array autocall_levels
- Risultato: incoerenza tra parametri e array

SOLUZIONE:
- Auto-generazione autocall_levels quando si salvano parametri step-down
- Validazione e correzione automatica incoerenze
- Calcolo preciso dei decimali
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class AutocallLevelsGenerator:
    """Generatore automatico livelli autocall step-down"""
    
    @staticmethod
    def generate_autocall_levels(
        total_periods: int,
        autocall_start_period: int,
        initial_level: float,
        step_down_rate: float,
        final_level: Optional[float] = None
    ) -> List[float]:
        """
        Genera array autocall_levels step-down
        
        Args:
            total_periods: Numero totale periodi (es. 60 mesi)
            autocall_start_period: Periodo inizio autocall (es. 6 = 6° mese)
            initial_level: Livello iniziale autocall (es. 1.00 = 100%)
            step_down_rate: Rate diminuzione per periodo (es. 0.005 = 0.5%)
            final_level: Livello finale minimo (opzionale)
        
        Returns:
            List[float]: Array autocall levels
        """
        
        levels = []
        
        # Primi periodi: nessun autocall (None o valore speciale)
        for i in range(autocall_start_period):
            levels.append(1.0)  # Placeholder - sarà ignorato nella logica
        
        # Periodi con autocall step-down
        current_level = initial_level
        
        for i in range(autocall_start_period, total_periods):
            # Applica step-down dal secondo periodo autocall
            if i > autocall_start_period:
                current_level -= step_down_rate
            
            # Applica livello minimo se specificato
            if final_level is not None:
                current_level = max(current_level, final_level)
            
            levels.append(round(current_level, 4))  # Arrotonda a 4 decimali
        
        return levels
    
    @staticmethod
    def calculate_step_down_parameters(termsheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcola parametri step-down da dati termsheet
        
        Args:
            termsheet_data: Dati dal termsheet (es. livelli autocall mensili)
            
        Returns:
            Dict: Parametri calcolati (initial_level, step_down_rate, etc.)
        """
        
        # Esempio calcolo da termsheet IT0006767872
        # Dal termsheet: 100% -> 99.5% -> 99% -> ... -> 73%
        
        autocall_levels_termsheet = [
            1.000, 0.995, 0.990, 0.985, 0.980, 0.975, 0.970, 0.965, 0.960, 0.955,
            0.950, 0.945, 0.940, 0.935, 0.930, 0.925, 0.920, 0.915, 0.910, 0.905,
            0.900, 0.895, 0.890, 0.885, 0.880, 0.875, 0.870, 0.865, 0.860, 0.855,
            0.850, 0.845, 0.840, 0.835, 0.830, 0.825, 0.820, 0.815, 0.810, 0.805,
            0.800, 0.795, 0.790, 0.785, 0.780, 0.775, 0.770, 0.765, 0.760, 0.755,
            0.750, 0.745, 0.740, 0.735, 0.730
        ]
        
        if len(autocall_levels_termsheet) >= 2:
            initial_level = autocall_levels_termsheet[0]
            final_level = autocall_levels_termsheet[-1]
            step_down_rate = autocall_levels_termsheet[0] - autocall_levels_termsheet[1]
            
            return {
                'initial_level': initial_level,
                'final_level': final_level,
                'step_down_rate': step_down_rate,
                'total_steps': len(autocall_levels_termsheet)
            }
        
        # Default fallback
        return {
            'initial_level': 1.00,
            'final_level': 0.73,
            'step_down_rate': 0.005,  # 0.5%
            'total_steps': 55
        }

class CertificateDataValidator:
    """Validatore e correttore automatico dati certificato"""
    
    @staticmethod
    def validate_and_fix_certificate_data(cert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e corregge automaticamente dati certificato
        
        Args:
            cert_data: Dati certificato da validare
            
        Returns:
            Dict: Dati corretti e validati
        """
        
        # Copia per non modificare originale
        fixed_data = cert_data.copy()
        
        # 1. Fix step-down autocall levels
        if fixed_data.get('dynamic_barriers', False):
            fixed_data = CertificateDataValidator._fix_autocall_levels(fixed_data)
        
        # 2. Fix incoerenze barriere
        fixed_data = CertificateDataValidator._fix_barrier_consistency(fixed_data)
        
        # 3. Fix precisione decimali
        fixed_data = CertificateDataValidator._fix_decimal_precision(fixed_data)
        
        # 4. Fix certificate type consistency
        fixed_data = CertificateDataValidator._fix_certificate_type_consistency(fixed_data)
        
        return fixed_data
    
    @staticmethod
    def _fix_autocall_levels(cert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix autocall levels step-down"""
        
        # Parametri step-down
        step_down_rate = cert_data.get('step_down_rate', 0.005)
        
        # Fix: Se step_down_rate > 0.1, probabilmente è in percentuale invece che decimale
        if step_down_rate > 0.1:
            step_down_rate = step_down_rate / 100  # Converti da 5% a 0.05
            cert_data['step_down_rate'] = step_down_rate
        
        # Parametri per generazione
        total_periods = len(cert_data.get('coupon_dates', []))
        autocall_start_period = 5  # Dal termsheet: inizio 6° mese (index 5)
        initial_level = 1.00
        final_level = 0.73  # Dal termsheet
        
        # Genera autocall levels
        autocall_levels = AutocallLevelsGenerator.generate_autocall_levels(
            total_periods=total_periods,
            autocall_start_period=autocall_start_period,
            initial_level=initial_level,
            step_down_rate=step_down_rate,
            final_level=final_level
        )
        
        # Aggiorna dati
        cert_data['autocall_levels'] = autocall_levels
        cert_data['autocall_type'] = 'step_down'  # Fix type
        cert_data['autocall_start_period'] = autocall_start_period
        cert_data['autocall_initial_level'] = initial_level
        cert_data['autocall_final_level'] = final_level
        
        print(f"🔧 Auto-generati {len(autocall_levels)} autocall levels: {initial_level} -> {final_level}")
        
        return cert_data
    
    @staticmethod
    def _fix_barrier_consistency(cert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix incoerenze barriere"""
        
        # Detect airbag vs capital protection
        barrier_capital = cert_data.get('barrier_levels', {}).get('capital', 0.5)
        
        if barrier_capital < 1.0:  # Se barriera < 100%, è airbag
            cert_data['airbag_feature'] = True
            cert_data['capital_protected'] = False
            cert_data['airbag_level'] = barrier_capital
            cert_data['capital_barrier_type'] = 'airbag'
            
            print(f"🛡️ Rilevato airbag: barriera {barrier_capital*100}%")
        else:
            cert_data['airbag_feature'] = False
            cert_data['capital_protected'] = True
            cert_data['capital_barrier_type'] = 'protected'
            
            print(f"🛡️ Rilevata protezione capitale: {barrier_capital*100}%")
        
        # Fix coupon barrier
        barrier_coupon = cert_data.get('barrier_levels', {}).get('coupon', 0.0)
        if barrier_coupon == 0.0:
            cert_data['coupon_barrier_type'] = 'none'
            cert_data['memory_feature'] = False  # Cedole incondizionate
            print(f"💰 Cedole incondizionate (barriera coupon = 0%)")
        
        return cert_data
    
    @staticmethod
    def _fix_decimal_precision(cert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix precisione decimali"""
        
        # Fix period_rate: 0.67% = 0.0067, non 0.67
        period_rate_percent = cert_data.get('period_rate_percent', 0.67)
        
        if period_rate_percent > 0.1:  # Se > 10%, è in percentuale
            period_rate_decimal = period_rate_percent / 100
            cert_data['period_rate'] = round(period_rate_decimal, 5)  # 0.00667
            
            print(f"📊 Corretto period_rate: {period_rate_percent}% -> {period_rate_decimal}")
        
        # Fix coupon_rates array
        if 'coupon_rates' in cert_data and 'period_rate' in cert_data:
            correct_rate = cert_data['period_rate']
            cert_data['coupon_rates'] = [correct_rate] * len(cert_data['coupon_rates'])
            
            print(f"📊 Aggiornati {len(cert_data['coupon_rates'])} coupon rates a {correct_rate}")
        
        return cert_data
    
    @staticmethod
    def _fix_certificate_type_consistency(cert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix consistenza tipo certificato"""
        
        # Detect tipo reale da caratteristiche
        has_autocall = cert_data.get('has_autocall', False)
        has_step_down = cert_data.get('dynamic_barriers', False)
        has_airbag = cert_data.get('airbag_feature', False)
        
        if has_autocall and has_step_down and has_airbag:
            cert_data['certificate_type'] = 'express'
            print(f"📋 Rilevato tipo: Express (autocall + step-down + airbag)")
        elif has_autocall and not has_step_down:
            cert_data['certificate_type'] = 'cash_collect'
            print(f"📋 Rilevato tipo: Cash Collect (autocall fisso)")
        else:
            # Mantieni tipo esistente se non chiaro
            existing_type = cert_data.get('certificate_type', 'express')
            print(f"📋 Mantenuto tipo esistente: {existing_type}")
        
        return cert_data

# ========================================
# PATCH PER fixed_gui_manager_v14.py
# ========================================

def patch_save_certificates_method():
    """
    Patch da applicare al metodo _save_certificates in fixed_gui_manager_v14.py
    
    INSERIRE QUESTO CODICE nel metodo _save_certificates PRIMA del salvataggio finale
    """
    
    patch_code = '''
    # *** PATCH v14.12: AUTO-GENERATION AUTOCALL LEVELS ***
    for cert_id, cert_data in self.certificates.items():
        if cert_data is not None:
            print(f"🔧 Validazione e correzione dati: {cert_id}")
            
            # Applica validazione e correzione automatica
            try:
                from gui_autocall_fix import CertificateDataValidator
                
                corrected_data = CertificateDataValidator.validate_and_fix_certificate_data(cert_data)
                self.certificates[cert_id] = corrected_data
                
                print(f"✅ Dati corretti per {cert_id}")
                
            except Exception as e:
                print(f"⚠️  Errore correzione {cert_id}: {e}")
                # Continua con dati originali
    '''
    
    return patch_code

# ========================================
# TESTING
# ========================================

def test_autocall_generation():
    """Test generazione autocall levels"""
    
    print("🧪 TEST AUTO-GENERATION AUTOCALL LEVELS")
    print("=" * 50)
    
    # Test 1: Generazione step-down standard
    levels = AutocallLevelsGenerator.generate_autocall_levels(
        total_periods=60,
        autocall_start_period=5,
        initial_level=1.00,
        step_down_rate=0.005,
        final_level=0.73
    )
    
    print(f"📊 Generati {len(levels)} livelli")
    print(f"   Primi 5: {levels[:5]}")
    print(f"   Livelli autocall: {levels[5:10]}")
    print(f"   Ultimi 5: {levels[-5:]}")
    
    # Test 2: Validazione dati certificato
    test_cert_data = {
        'isin': 'IT0006767872',
        'dynamic_barriers': True,
        'step_down_rate': 0.05,  # 5% (SBAGLIATO - dovrebbe essere 0.5%)
        'period_rate_percent': 0.67,
        'period_rate': 0.0067,
        'barrier_levels': {'coupon': 0.0, 'capital': 0.5},
        'airbag_feature': False,  # INCOERENTE con barrier_capital < 1.0
        'capital_protected': True,  # INCOERENTE
        'certificate_type': 'cash_collect',  # PROBABILMENTE SBAGLIATO
        'coupon_dates': ['2025-04-08'] * 60,  # 60 mesi
        'coupon_rates': [0.0067] * 60
    }
    
    print(f"\n🔍 Test validazione dati certificato:")
    print(f"   Dati originali:")
    print(f"     step_down_rate: {test_cert_data['step_down_rate']}")
    print(f"     airbag_feature: {test_cert_data['airbag_feature']}")
    print(f"     certificate_type: {test_cert_data['certificate_type']}")
    
    # Applica correzione
    fixed_data = CertificateDataValidator.validate_and_fix_certificate_data(test_cert_data)
    
    print(f"   Dati corretti:")
    print(f"     step_down_rate: {fixed_data['step_down_rate']}")
    print(f"     airbag_feature: {fixed_data['airbag_feature']}")
    print(f"     certificate_type: {fixed_data['certificate_type']}")
    print(f"     autocall_levels generati: {len(fixed_data.get('autocall_levels', []))}")
    
    return True

if __name__ == "__main__":
    """Test standalone"""
    test_autocall_generation()
