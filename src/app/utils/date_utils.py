# ========================================
# *** VERSIONE CORRETTA *** - CALCOLO DATE ROBUSTO
# ========================================
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from typing import List, Tuple
from app.core.real_certificate_integration import RealCertificateConfig


class DateCalculationUtils:
    """Utility per calcolo date (ora in un file dedicato per evitare import circolari)"""
    
    @staticmethod
    def calculate_coupon_dates_robust(start_date: datetime, end_date: datetime, 
                                    frequency: str) -> List[datetime]:
        """*** VERSIONE ROBUSTA *** - Calcolo date senza errore 'day out of range'"""
        
        print(f"📅 Calcolo date robusto v15:")
        print(f"   Start: {start_date.strftime('%Y-%m-%d')}")
        print(f"   End: {end_date.strftime('%Y-%m-%d')}")
        print(f"   Frequency: {frequency}")
        
        # Mapping frequenze
        interval_months = {
            "Mensile": 1, "M": 1,
            "Bimestrale": 2, "B": 2, # Aggiunto Bimestrale
            "Trimestrale": 3, "Q": 3,
            "Quadrimestrale": 4, "R": 4, # Aggiunto Quadrimestrale
            "Semestrale": 6, "S": 6,
            "Annuale": 12, "A": 12
        }
        
        if frequency not in interval_months:
            raise ValueError(f"Frequenza non supportata: {frequency}")
        
        months_interval = interval_months[frequency]
        coupon_dates = []
        
        # Inizia dal primo periodo
        current_year = start_date.year
        current_month = start_date.month + months_interval
        target_day = start_date.day
        
        # Aggiusta anno se necessario
        while current_month > 12:
            current_month -= 12
            current_year += 1
        
        print(f"   Primo periodo: {current_year}-{current_month:02d}-{target_day:02d}")
        
        # Genera tutte le date
        iteration = 0
        while iteration < 500:  # Safety limit aumentato
            
            # *** FIX CRITICO *** - Gestisce giorni inesistenti nel mese
            try:
                # Verifica se il giorno esiste nel mese
                last_day_of_month = calendar.monthrange(current_year, current_month)[1]
                actual_day = min(target_day, last_day_of_month)
                
                current_date = datetime(current_year, current_month, actual_day)
                
                # Rimuovo la stampa per non affollare il log
                # print(f"   Data generata: {current_date.strftime('%Y-%m-%d')}")
                
                # Verifica se supera la data di fine
                if current_date > end_date:
                    # print(f"   Fermato: data supera end_date")
                    break
                
                coupon_dates.append(current_date)
                
            except ValueError as date_error:
                print(f"   ❌ Errore creazione data {current_year}-{current_month:02d}-{actual_day:02d}: {date_error}")
                
                # Fallback: usa ultimo giorno del mese
                try:
                    last_day = calendar.monthrange(current_year, current_month)[1]
                    current_date = datetime(current_year, current_month, last_day)
                    
                    if current_date <= end_date:
                        coupon_dates.append(current_date)
                        print(f"   🔧 Fallback data: {current_date.strftime('%Y-%m-%d')}")
                    else:
                        break
                        
                except Exception as fallback_error:
                    print(f"   ❌ Anche fallback fallito: {fallback_error}")
                    break
            
            # Incrementa al prossimo periodo
            current_month += months_interval
            while current_month > 12:
                current_month -= 12
                current_year += 1
            
            iteration += 1
        
        # *** VERIFICA FINALE *** - Assicura che maturity sia inclusa
        if coupon_dates and coupon_dates[-1] != end_date:
            # Solo se maturity è dopo l'ultima cedola
            if end_date > coupon_dates[-1]:
                coupon_dates.append(end_date)
                print(f"   📌 Maturity aggiunta: {end_date.strftime('%Y-%m-%d')}")
        elif not coupon_dates:
            # Caso estremo: almeno maturity
            coupon_dates.append(end_date)
            print(f"   🚨 Solo maturity: {end_date.strftime('%Y-%m-%d')}")
        
        print(f"📊 Totale {len(coupon_dates)} date cedole generate (robusto v15)")
        
        # Verifica ordine cronologico
        for i in range(1, len(coupon_dates)):
            if coupon_dates[i] <= coupon_dates[i-1]:
                print(f"   ⚠️  Warning: date non in ordine cronologico")
                break
        
        return coupon_dates
    
    @staticmethod
    def validate_coupon_schedule(coupon_dates: List[datetime], 
                               coupon_rates: List[float]) -> Tuple[bool, str]:
        """Valida coerenza schedule cedole"""
        
        if not coupon_dates:
            return False, "Nessuna data cedola specificata"
        
        if not coupon_rates:
            return False, "Nessun tasso cedola specificato"
        
        if len(coupon_dates) != len(coupon_rates):
            return False, f"Mismatch: {len(coupon_dates)} date vs {len(coupon_rates)} tassi"
        
        # Verifica ordine cronologico
        for i in range(1, len(coupon_dates)):
            if coupon_dates[i] <= coupon_dates[i-1]:
                return False, f"Date non in ordine cronologico: {coupon_dates[i-1]} >= {coupon_dates[i]}"
        
        # Verifica tassi validi
        for i, rate in enumerate(coupon_rates):
            if not (0 <= rate <= 1):
                return False, f"Tasso {i+1} fuori range [0,1]: {rate}"
        
        return True, "Schedule valida"

    @staticmethod
    def generate_dynamic_barrier_schedule(cert_config: RealCertificateConfig) -> dict:
        """
        Genera una schedule di barriere dinamiche basata sulla configurazione del certificato.
        Restituisce un dizionario { 'YYYY-MM-DD': livello_barriera_decimale }.
        """
        # 1. Controlla se la funzionalità è attiva
        if not getattr(cert_config, 'dynamic_barrier_feature', False):
            return {}

        # 2. Recupera i parametri necessari in modo sicuro
        try:
            issue_date = cert_config.issue_date
            coupon_dates = cert_config.coupon_dates
            start_level = cert_config.dynamic_barrier_start_level
            step_rate = cert_config.step_down_rate
            final_level = cert_config.dynamic_barrier_end_level
            delay_months = cert_config.observation_delay_months or 0 # Default a 0 se None

            if not all([issue_date, coupon_dates, start_level is not None, step_rate is not None, final_level is not None]):
                raise ValueError("Parametri per barriera dinamica mancanti o incompleti.")

        except (AttributeError, ValueError) as e:
            print(f"⚠️  Impossibile generare schedule barriera dinamica: {e}")
            return {}

        # 3. Calcola la data di inizio per lo step-down
        first_observation_date = issue_date + relativedelta(months=delay_months)
        
        schedule = {}
        steps_taken = 0

        # 4. Itera sulle date di osservazione (cedole) per costruire la schedule
        for obs_date in sorted(coupon_dates):
            current_level = start_level # La barriera di partenza è sempre il livello iniziale

            # Lo step-down si applica solo a partire dalla data di osservazione valida
            if obs_date >= first_observation_date:
                # Calcola il livello corrente in base ai passi già effettuati
                calculated_level = start_level - (steps_taken * step_rate)
                current_level = max(calculated_level, final_level) # Assicura di non scendere sotto il livello finale
                steps_taken += 1
            
            # Formatta la data come stringa 'YYYY-MM-DD' per la chiave del dizionario
            schedule[obs_date.strftime('%Y-%m-%d')] = round(current_level, 5) # Arrotonda per precisione

        print(f"✅ Schedule barriera dinamica generata con {len(schedule)} date.")
        return schedule
