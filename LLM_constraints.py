from datetime import date, timedelta, datetime
from ortools.sat.python import cp_model

def add_preferences(model, shifts, lavoratori, giorni_totali, turni_totali, DAYS_LIST):
    objective_terms = []
    
    # --- MAPPING COSTANTI ---
    SHIFT_MAP = {
        "MORNING": 0,
        "AFTERNOON": 1,
        "NIGHT": 2
    }
    
    WEEKDAY_MAP = {
        "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3,
        "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6
    }
    
    # Mappatura festività per l'orizzonte temporale corrente (Dic 2026 - Gen 2027)
    # Le date nel JSON (2025) sono obsolete, usiamo le date reali del periodo di pianificazione.
    HOLIDAY_MAP = {
        "Christmas Eve": date(2026, 12, 24),
        "Christmas Day": date(2026, 12, 25),
        "St. Stephen's Day": date(2026, 12, 26),
        "New Year's Eve": date(2026, 12, 31),
        "New Year's Day": date(2027, 1, 1)
    }
    
    # Pesi funzione obiettivo
    WEIGHT_PREF_SHIFT = 1       # Ricompensa per turno preferito
    WEIGHT_PREF_DAY_OFF = 5     # Ricompensa per giorno libero preferito
    PENALTY_DISLIKED_SHIFT = 10 # Penalità per turno non gradito (tipo)
    PENALTY_DISLIKED_HOLIDAY = 20 # Penalità per turno in festività non gradita
    
    # --- DATI PREFERENZE (EMBEDDATI DAL JSON FORNITO) ---
    preferences_data = [
        {"worker_id": 0, "preferred_shift": "MORNING", "preferred_day_off": "MONDAY", "disliked_shifts": ["NIGHT", "Christmas Day"], "unavailable_dates": ["2025-12-25"]},
        {"worker_id": 1, "preferred_shift": "AFTERNOON", "preferred_day_off": "FRIDAY", "disliked_shifts": ["NIGHT"], "unavailable_dates": []},
        {"worker_id": 2, "preferred_shift": "NIGHT", "preferred_day_off": "SUNDAY", "disliked_shifts": [], "unavailable_dates": ["2025-12-31"]},
        {"worker_id": 3, "preferred_shift": "MORNING", "preferred_day_off": "SATURDAY", "disliked_shifts": ["NIGHT", "Christmas Day", "New Year's Day"], "unavailable_dates": ["2025-12-25", "2026-01-01"]},
        {"worker_id": 4, "preferred_shift": "AFTERNOON", "preferred_day_off": "WEDNESDAY", "disliked_shifts": ["NIGHT"], "unavailable_dates": []},
        {"worker_id": 5, "preferred_shift": "MORNING", "preferred_day_off": "SATURDAY", "disliked_shifts": ["NIGHT", "New Year's Day"], "unavailable_dates": ["2026-01-01"]},
        {"worker_id": 6, "preferred_shift": "NIGHT", "preferred_day_off": "TUESDAY", "disliked_shifts": ["Christmas Day"], "unavailable_dates": ["2025-12-25"]},
        {"worker_id": 7, "preferred_shift": "AFTERNOON", "preferred_day_off": "THURSDAY", "disliked_shifts": ["NIGHT", "Christmas Day", "St. Stephen's Day"], "unavailable_dates": ["2025-12-25", "2025-12-26"]},
        {"worker_id": 8, "preferred_shift": "MORNING", "preferred_day_off": "SUNDAY", "disliked_shifts": ["NIGHT"], "unavailable_dates": []},
        {"worker_id": 9, "preferred_shift": "AFTERNOON", "preferred_day_off": "MONDAY", "disliked_shifts": ["Christmas Eve", "New Year's Eve"], "unavailable_dates": ["2025-12-24", "2025-12-31"]},
        {"worker_id": 10, "preferred_shift": "AFTERNOON", "preferred_day_off": "FRIDAY", "disliked_shifts": ["Christmas Eve", "New Year's Eve"], "unavailable_dates": ["2025-12-24", "2025-12-31"]},
        {"worker_id": 11, "preferred_shift": "MORNING", "preferred_day_off": "THURSDAY", "disliked_shifts": ["NIGHT", "New Year's Day"], "unavailable_dates": ["2026-01-01"]},
        {"worker_id": 12, "preferred_shift": "AFTERNOON", "preferred_day_off": "TUESDAY", "disliked_shifts": ["Christmas Eve", "Christmas Day"], "unavailable_dates": ["2025-12-24", "2025-12-25"]}
    ]
    
    # Creiamo un dizionario per accesso rapido: worker_id -> prefs
    prefs_dict = {p["worker_id"]: p for p in preferences_data}
    
    # Mappa data -> indice giorno (g) per lookup veloce
    date_to_g = {d: i for i, d in enumerate(DAYS_LIST)}
    
    for l in range(lavoratori):
        if l not in prefs_dict:
            continue
            
        pref = prefs_dict[l]
        
        # 1. DATE NON DISPONIBILI (Vincolo Hard)
        # Nota: le date nel JSON sono 2025, il piano è 2026/2027. 
        # Controlliamo comunque se cadono nel range per robustezza.
        for date_str in pref["unavailable_dates"]:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
                if d in date_to_g:
                    g = date_to_g[d]
                    # Il lavoratore non fa nessun turno quel giorno
                    model.add(sum(shifts[(l, g, t)] for t in range(turni_totali)) == 0)
            except ValueError:
                pass # Formato data non valido
        
        # 2. TURNI PREFERITI (Soft Constraint - Ricompensa)
        pref_shift_name = pref["preferred_shift"]
        if pref_shift_name in SHIFT_MAP:
            t_pref = SHIFT_MAP[pref_shift_name]
            for g in range(giorni_totali):
                # Aggiungiamo termine positivo se fa il turno preferito
                objective_terms.append(shifts[(l, g, t_pref)] * WEIGHT_PREF_SHIFT)
        
        # 3. GIORNO LIBERO PREFERITO (Soft Constraint - Ricompensa)
        pref_day_off_name = pref["preferred_day_off"]
        if pref_day_off_name in WEEKDAY_MAP:
            target_weekday = WEEKDAY_MAP[pref_day_off_name]
            for g in range(giorni_totali):
                if DAYS_LIST[g].weekday() == target_weekday:
                    # Creiamo una variabile booleana: 1 se il lavoratore è libero quel giorno
                    is_off = model.new_bool_var(f"off_l{l}_g{g}")
                    # is_off == 1 <=> sum(shifts) == 0
                    model.add(sum(shifts[(l, g, t)] for t in range(turni_totali)) == 0).only_enforce_if(is_off)
                    model.add(sum(shifts[(l, g, t)] for t in range(turni_totali)) >= 1).only_enforce_if(is_off.Not())
                    objective_terms.append(is_off * WEIGHT_PREF_DAY_OFF)
        
        # 4. TURNI NON GRADITI (Soft Constraint - Penalità)
        for disliked in pref["disliked_shifts"]:
            # Caso A: È un tipo di turno (MORNING, AFTERNOON, NIGHT)
            if disliked in SHIFT_MAP:
                t_dislike = SHIFT_MAP[disliked]
                for g in range(giorni_totali):
                    # Penalità se assegnato a quel turno
                    objective_terms.append(shifts[(l, g, t_dislike)] * (-PENALTY_DISLIKED_SHIFT))
            
            # Caso B: È una festività nominata (Christmas Day, etc.)
            elif disliked in HOLIDAY_MAP:
                holiday_date = HOLIDAY_MAP[disliked]
                if holiday_date in date_to_g:
                    g = date_to_g[holiday_date]
                    # Penalità se lavora QUALSIASI turno in quel giorno
                    # Creiamo var ausiliaria per linearizzare: worked_that_day = OR(shifts)
                    worked = model.new_bool_var(f"worked_l{l}_holiday_{disliked.replace(' ', '_')}")
                    model.add_max_equality(worked, [shifts[(l, g, t)] for t in range(turni_totali)])
                    objective_terms.append(worked * (-PENALTY_DISLIKED_HOLIDAY))
    
    return objective_terms