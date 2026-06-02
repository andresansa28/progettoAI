from datetime import date, timedelta

# Date del problema
START_DATE = date(2026, 12, 7)
END_DATE = date(2027, 1, 6)

DAYS = []

current = START_DATE

while current <= END_DATE:
    DAYS.append(current)
    current += timedelta(days=1)
    
WEEKS = []

#range(inizio, fine, passo)
for start in range(0, len(DAYS), 7): 
    week = list(range(start, min(start + 7, len(DAYS))))
    WEEKS.append(week)
    

# Turni
MORNING = 0
AFTERNOON = 1
NIGHT = 2

SHIFT_NAMES = {
    MORNING: "Morning",
    AFTERNOON: "Afternoon",
    NIGHT: "Night"
}

SHIFT_HOURS = {
    MORNING: 6,
    AFTERNOON: 6,
    NIGHT: 12
}

# Vincoli globali
MIN_WORKERS_PER_SHIFT = 1
MAX_HOURS_PER_WEEK = 36
SHIFTS_PER_MONTH = 25
REST_DAYS_AFTER_NIGHT = 2