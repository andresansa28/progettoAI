from datetime import date, timedelta

# Date del problema
START_DATE = date(2026, 12, 7)
END_DATE = date(2027, 1, 6)

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
MIN_WORKERS_PER_SHIFT = 2
MAX_HOURS_PER_WEEK = 36
SHIFTS_PER_MONTH = 25
REST_DAYS_AFTER_NIGHT = 2