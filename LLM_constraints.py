
from datetime import date, timedelta, datetime

def add_preferences(model, shifts, lavoratori, giorni_totali, turni_totali, DAYS_LIST):
    objective_terms = []
    
    # Mappatura dei turni
    SHIFT_MAP = {
        "MORNING": 0,
        "AFTERNOON": 1,
        "NIGHT": 2
    }

    # Mappatura dei giorni della settimana (Python weekday: Monday=0, Sunday=6)
    WEEKDAY_MAP = {
        "MONDAY": 0,
        "TUESDAY": 1,
        "WEDNESDAY": 2,
        "THURSDAY": 3,
        "FRIDAY": 4,
        "SATURDAY": 5,
        "SUNDAY": 6
    }

    # Mappatura delle festività (mese, giorno)
    HOLIDAY_MAP = {
        "Christmas Eve": (12, 24),
        "Christmas Day": (12, 25),
        "St. Stephen's Day": (12, 26),
        "New Year's Eve": (12, 31),
        "New Year's Day": (1, 1)
    }

    # Dataset delle preferenze dei lavoratori
    PREFERENCES_DATA = [
        {
            "worker_id": 0,
            "preferred_shift": "MORNING",
            "preferred_day_off": "MONDAY",
            "disliked_shifts": ["NIGHT", "Christmas Day"],
            "unavailable_dates": ["2025-12-25"]
        },
        {
            "worker_id": 1,
            "preferred_shift": "AFTERNOON",
            "preferred_day_off": "FRIDAY",
            "disliked_shifts": ["NIGHT"],
            "unavailable_dates": []
        },
        {
            "worker_id": 2,
            "preferred_shift": "NIGHT",
            "preferred_day_off": "SUNDAY",
            "disliked_shifts": [],
            "unavailable_dates": ["2025-12-31"]
        },
        {
            "worker_id": 3,
            "preferred_shift": "MORNING",
            "preferred_day_off": "SATURDAY",
            "disliked_shifts": ["NIGHT", "Christmas Day", "New Year's Day"],
            "unavailable_dates": ["2025-12-25", "2026-01-01"]
        },
        {
            "worker_id": 4,
            "preferred_shift": "AFTERNOON",
            "preferred_day_off": "WEDNESDAY",
            "disliked_shifts": ["NIGHT"],
            "unavailable_dates": []
        },
        {
            "worker_id": 5,
            "preferred_shift": "MORNING",
            "preferred_day_off": "SATURDAY",
            "disliked_shifts": ["NIGHT", "New Year's Day"],
            "unavailable_dates": ["2026-01-01"]
        },
        {
            "worker_id": 6,
            "preferred_shift": "NIGHT",
            "preferred_day_off": "TUESDAY",
            "disliked_shifts": ["Christmas Day"],
            "unavailable_dates": ["2025-12-25"]
        },
        {
            "worker_id": 7,
            "preferred_shift": "AFTERNOON",
            "preferred_day_off": "THURSDAY",
            "disliked_shifts": ["NIGHT", "Christmas Day", "St. Stephen's Day"],
            "unavailable_dates": ["2025-12-25", "2025-12-26"]
        },
        {
            "worker_id": 8,
            "preferred_shift": "MORNING",
            "preferred_day_off": "SUNDAY",
            "disliked_shifts": ["NIGHT"],
            "unavailable_dates": []
        },
        {
            "worker_id": 9,
            "preferred_shift": "AFTERNOON",
            "preferred_day_off": "MONDAY",
            "disliked_shifts": ["Christmas Eve", "New Year's Eve"],
            "unavailable_dates": ["2025-12-24", "2025-12-31"]
        },
        {
            "worker_id": 10,
            "preferred_shift": "AFTERNOON",
            "preferred_day_off": "FRIDAY",
            "disliked_shifts": ["Christmas Eve", "New Year's Eve"],
            "unavailable_dates": ["2025-12-24", "2025-12-31"]
        },
        {
            "worker_id": 11,
            "preferred_shift": "MORNING",
            "preferred_day_off": "THURSDAY",
            "disliked_shifts": ["NIGHT", "New Year's Day"],
            "unavailable_dates": ["2026-01-01"]
        },
        {
            "worker_id": 12,
            "preferred_shift": "AFTERNOON",
            "preferred_day_off": "TUESDAY",
            "disliked_shifts": ["Christmas Eve", "Christmas Day"],
            "unavailable_dates": ["2025-12-24", "2025-12-25"]
        }
    ]

    # Helper per mappare le date (gestisce il disallineamento dell'anno nel JSON)
    def get_day_index(target_date):
        # Cerca corrispondenza esatta
        for idx, d in enumerate(DAYS_LIST):
            if d == target_date:
                return idx
        # Fallback: cerca corrispondenza per mese e giorno (ignora l'anno)
        for idx, d in enumerate(DAYS_LIST):
            if d.month == target_date.month and d.day == target_date.day:
                return idx
        return None

    # Helper per trovare l'indice del giorno di una festività specifica
    def get_holiday_index(holiday_name):
        if holiday_name in HOLIDAY_MAP:
            m, d = HOLIDAY_MAP[holiday_name]
            for idx, day_date in enumerate(DAYS_LIST):
                if day_date.month == m and day_date.day == d:
                    return idx
        return None

    # Pesi per la funzione obiettivo (da massimizzare)
    WEIGHT_PREF_SHIFT = 10       # Guadagno giornaliero se lavora nel turno preferito
    WEIGHT_PREF_DAY_OFF = -12    # Penale se lavora nel giorno in cui preferisce il riposo
    WEIGHT_DISLIKED_SHIFT = -8   # Penale se lavora in un turno sgradito
    WEIGHT_DISLIKED_HOLIDAY = -20 # Penale se lavora in un giorno festivo sgradito

    for pref in PREFERENCES_DATA:
        l = pref["worker_id"]
        if l >= lavoratori:
            continue

        # 1. TURNO PREFERITO (Soft Constraint - Reward)
        pref_shift_str = pref.get("preferred_shift")
        if pref_shift_str in SHIFT_MAP:
            t_idx = SHIFT_MAP[pref_shift_str]
            for g in range(giorni_totali):
                objective_terms.append(WEIGHT_PREF_SHIFT * shifts[(l, g, t_idx)])

        # 2. GIORNO DI RIPOSO PREFERITO (Soft Constraint - Penalty se lavora)
        pref_day_off_str = pref.get("preferred_day_off")
        if pref_day_off_str in WEEKDAY_MAP:
            target_weekday = WEEKDAY_MAP[pref_day_off_str]
            for g in range(giorni_totali):
                if DAYS_LIST[g].weekday() == target_weekday:
                    for t in range(turni_totali):
                        objective_terms.append(WEIGHT_PREF_DAY_OFF * shifts[(l, g, t)])

        # 3. TURNI E FESTIVITÀ SGRADITI (Soft Constraint - Penalty)
        for disliked in pref.get("disliked_shifts", []):
            if disliked in SHIFT_MAP:
                # È un turno sgradito generico (es. NIGHT)
                t_idx = SHIFT_MAP[disliked]
                for g in range(giorni_totali):
                    objective_terms.append(WEIGHT_DISLIKED_SHIFT * shifts[(l, g, t_idx)])
            elif disliked in HOLIDAY_MAP:
                # È una festività specifica sgradita (es. Christmas Day)
                g_idx = get_holiday_index(disliked)
                if g_idx is not None:
                    for t in range(turni_totali):
                        objective_terms.append(WEIGHT_DISLIKED_HOLIDAY * shifts[(l, g_idx, t)])

        # 4. DATE DI INDISPONIBILITÀ (Hard Constraint - Forza a 0)
        for date_str in pref.get("unavailable_dates", []):
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                g_idx = get_day_index(target_date)
                if g_idx is not None:
                    for t in range(turni_totali):
                        model.add(shifts[(l, g_idx, t)] == 0)
            except ValueError:
                # Salta in caso di formati data non validi nel JSON
                continue

    return objective_terms