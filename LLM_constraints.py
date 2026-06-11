# worker_preferences.py
# Modulo generato automaticamente per formalizzare hard constraints e soft preferences

# --- 1. HARD CONSTRAINTS ---
UNAVAILABLE_DATES = {
    0: ["2025-12-25"],
    1: [],
    2: ["2025-12-31"],
    3: ["2025-12-25", "2026-01-01"],
    4: [],
    5: ["2026-01-01"],
    6: ["2025-12-25"],
    7: ["2025-12-25", "2025-12-26"],
    8: [],
    9: ["2025-12-24", "2025-12-31"],
    10: ["2025-12-24", "2025-12-31"],
    11: ["2026-01-01"],
    12: ["2025-12-24", "2025-12-25"]
}

# --- 2. SOFT CONSTRAINTS & WEIGHTS ---
BONUS_PREFERRED_SHIFT = 5
PENALTY_DISLIKED_SHIFT = -10
BONUS_DAY_OFF = 10

WORKER_PREFS = {
    0: {"shift": "MORNING", "day_off": "MONDAY", "disliked": ["NIGHT", "Christmas Day"]},
    1: {"shift": "AFTERNOON", "day_off": "FRIDAY", "disliked": ["NIGHT"]},
    2: {"shift": "NIGHT", "day_off": "SUNDAY", "disliked": []},
    3: {"shift": "MORNING", "day_off": "SATURDAY", "disliked": ["NIGHT", "Christmas Day", "New Year's Day"]},
    4: {"shift": "AFTERNOON", "day_off": "WEDNESDAY", "disliked": ["NIGHT"]},
    5: {"shift": "MORNING", "day_off": "SATURDAY", "disliked": ["NIGHT", "New Year's Day"]},
    6: {"shift": "NIGHT", "day_off": "TUESDAY", "disliked": ["Christmas Day"]},
    7: {"shift": "AFTERNOON", "day_off": "THURSDAY", "disliked": ["NIGHT", "Christmas Day", "St. Stephen's Day"]},
    8: {"shift": "MORNING", "day_off": "SUNDAY", "disliked": ["NIGHT"]},
    9: {"shift": "AFTERNOON", "day_off": "MONDAY", "disliked": ["Christmas Eve", "New Year's Eve"]},
    10: {"shift": "AFTERNOON", "day_off": "FRIDAY", "disliked": ["Christmas Eve", "New Year's Eve"]},
    11: {"shift": "MORNING", "day_off": "THURSDAY", "disliked": ["NIGHT", "New Year's Day"]},
    12: {"shift": "AFTERNOON", "day_off": "TUESDAY", "disliked": ["Christmas Eve", "Christmas Day"]}
}

# --- 3. PREFERENCE SCORING (Modello di Soddisfazione) ---
def evaluate_worker_satisfaction(worker_id, assigned_shifts_list, assigned_days_off_list):
    """
    Calcola il punteggio di soddisfazione per un singolo lavoratore.
    assigned_shifts_list: lista di stringhe (es. ["MORNING", "NIGHT", ...])
    assigned_days_off_list: lista di stringhe (es. ["MONDAY", "TUESDAY", ...])
    """
    if worker_id not in WORKER_PREFS:
        return 0
    
    prefs = WORKER_PREFS[worker_id]
    score = 0
    
    # Valutazione turni
    for shift in assigned_shifts_list:
        if shift == prefs["shift"]:
            score += BONUS_PREFERRED_SHIFT
        if shift in prefs["disliked"]:
            score += PENALTY_DISLIKED_SHIFT
            
    # Valutazione giorni di riposo
    for day in assigned_days_off_list:
        if day == prefs["day_off"]:
            score += BONUS_DAY_OFF
            
    return score