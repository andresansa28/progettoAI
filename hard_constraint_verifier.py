from config import *


class HardConstraintVerifier:

    def __init__(self, solver, shifts, lavoratori, giorni, turni):

        self.solver = solver
        self.shifts = shifts
        self.lavoratori = lavoratori
        self.giorni = giorni
        self.turni = turni

    # Verifica che ogni turno abbia almeno il numero minimo di lavoratori assegnati
    def verify_number_of_workers_per_shift(self):

        number_of_workers_errors = []

        for g in range(self.giorni):
            for t in range(self.turni):
                assigned_workers = sum(
                    self.solver.Value(self.shifts[(l, g, t)])
                    for l in range(self.lavoratori)
                )

                if assigned_workers < MIN_WORKERS_PER_SHIFT:
                    number_of_workers_errors.append(
                        f"Giorno {g}, turno {t}: "
                        f"{assigned_workers} lavoratori "
                        f"(minimo {MIN_WORKERS_PER_SHIFT})"
                    )
        return number_of_workers_errors

    # Verifica che ogni lavoratore sia assegnato a massimo un turno al giorno
    def verify_one_shift_per_day(self):

        one_shift_errors = []

        for l in range(self.lavoratori):
            for g in range(self.giorni):
                number_of_shifts_for_day = sum(
                    self.solver.Value(self.shifts[(l, g, t)]) for t in range(self.turni)
                )

                if number_of_shifts_for_day > 1:
                    one_shift_errors.append(
                        f"Vincolo violato: Il lavoratore {l} è assegnato a {number_of_shifts_for_day} turni il giorno {g} (massimo consentito: 1)"
                    )
        return one_shift_errors

    # Verifica che dopo ogni turno di notte, il lavoratore abbia 2 giorni di riposo
    def verify_night_shift_rest(self):

        night_shift_rest_errors = []

        for l in range(self.lavoratori):
            for g in range(self.giorni):
                if self.solver.Value(self.shifts[(l, g, NIGHT)]) == 1:
                    for r in range(1, REST_DAYS_AFTER_NIGHT + 1):
                        if (g + r < self.giorni): # Controllo per evitare index out of range
                            for t in range(self.turni):
                                if self.solver.Value(self.shifts[(l, g + r, t)]) == 1:
                                    night_shift_rest_errors.append(
                                        f"Vincolo violato: Il lavoratore {l}\n"
                                        f"ha effettuato un turno di Night il giorno {g} \n"
                                        f"ma è assegnato a un turno {SHIFT_NAMES[t]} il giorno {g + r} \n"
                                        f"(deve avere {REST_DAYS_AFTER_NIGHT} giorni di riposo)"
                                    )
        return night_shift_rest_errors

    # verifica che ogni lavoratore non superi i 25 turni al mese
    def verify_max_shifts_per_month(self):

        max_shifts_errors = []

        for l in range(self.lavoratori):
            total_shifts = sum(
                self.solver.Value(self.shifts[(l, g, t)])
                for g in range(self.giorni)
                for t in range(self.turni)
            )

            if total_shifts > SHIFTS_PER_MONTH:
                max_shifts_errors.append(
                    f"Vincolo violato: Il lavoratore {l} è assegnato a {total_shifts} turni al mese (massimo consentito: {SHIFTS_PER_MONTH})"
                )
        return max_shifts_errors

    # Verifica che il lavoratore non superi le 36 ore settimanali
    def verify_max_hours_per_week(self):

        max_hours_errors = []

        for l in range(self.lavoratori):

            # tutte le finestre mobili di 7 giorni
            for start_day in range(0,self.giorni,7):
                end_day = min(start_day+7,self.giorni)

                total_hours = sum(
                    self.solver.Value(self.shifts[(l, g, t)]) * SHIFT_HOURS[t]
                    for g in range(start_day, end_day)
                    for t in range(self.turni)
                )

                if total_hours > MAX_HOURS_PER_WEEK:
                    max_hours_errors.append(
                        f"Vincolo violato: Il lavoratore {l} "
                        f"è assegnato a {total_hours} ore "
                        f"nella finestra {start_day}-{start_day + 6} "
                        f"(massimo consentito: {MAX_HOURS_PER_WEEK} ore)"
                    )

        return max_hours_errors

    
    # Verifica che ogni lavoratore abbia almeno un giorno libero a settimana
    def verify_min_days_off_per_week(self):

        min_days_off_errors = []

        for l in range(self.lavoratori):
            for start_day in range(0, self.giorni, 7):
                # Limita l'ultimo giorno della settimana a self.giorni
                end_day = min(start_day + 7, self.giorni)
                
                total_shifts_in_week = sum(
                    self.solver.Value(self.shifts[(l, g, t)])
                    for g in range(start_day, end_day)
                    for t in range(self.turni)
                )

                # Calcola la lunghezza reale della finestra (potrebbe essere < 7 a fine mese)
                window_length = end_day - start_day
                if window_length != 7:
                    continue
                # Deve esserci almeno 1 giorno libero nella finestra considerata
                if total_shifts_in_week > window_length - 1:
                    min_days_off_errors.append(
                        f"Vincolo violato: Il lavoratore {l} è assegnato a {total_shifts_in_week} "
                        f"turni nella finestra che include i giorni {start_day}-{end_day - 1} "
                        f"(deve avere almeno un giorno libero)"
                    )
        return min_days_off_errors

    def verify_all_constraints(self):

        errors = []
        errors.extend(self.verify_number_of_workers_per_shift())
        errors.extend(self.verify_one_shift_per_day())
        errors.extend(self.verify_night_shift_rest())
        errors.extend(self.verify_max_shifts_per_month())
        errors.extend(self.verify_max_hours_per_week())
        errors.extend(self.verify_min_days_off_per_week())

        return errors
