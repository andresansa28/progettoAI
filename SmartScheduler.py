from ortools.sat.python import cp_model
from config import *


def worker_scheduling(lavoratori, giorni, turni):
    model = cp_model.CpModel()

    shifts = {}

    # Griglia dei turni: vale 1 se il lavoratore l lavora nel giorno g al turno t.
    for l in range(lavoratori):
        for g in range(giorni):
            for t in range(turni):
                shifts[(l, g, t)] = model.new_bool_var(f"l{l}_g{g}_t{t}")

    # Almeno 2 lavoratori per ogni turno.
    for g in range(giorni):
        for t in range(turni):
            model.add(
                sum(shifts[(l, g, t)] for l in range(lavoratori))
                >= MIN_WORKERS_PER_SHIFT
            )

    # Ogni lavoratore puo' fare al massimo un turno al giorno.
    for l in range(lavoratori):
        for g in range(giorni):
            model.add_at_most_one([shifts[(l, g, t)] for t in range(turni)])

    # Dopo ogni turno di notte, il lavoratore deve avere 2 giorni di riposo
    for l in range(lavoratori):
        for g in range(giorni - REST_DAYS_AFTER_NIGHT):
            for r in range(1, REST_DAYS_AFTER_NIGHT + 1):
                for t in range(turni):
                    model.add(shifts[(l, g + r, t)] == 0).only_enforce_if(
                        shifts[(l, g, NIGHT)]
                    )

    # Ogni lavoratore non deve superare le 36 ore settimanali.
    for l in range(lavoratori):
        for w in WEEKS:
            model.add(
                sum(
                    shifts[(l, g, t)] * SHIFT_HOURS[t]
                    for g in w
                    for t in range(turni)
                )
                <= MAX_HOURS_PER_WEEK
            )

    # Ogni lavoratore deve fare 25 turni al mese:
    # mattina = 1, pomeriggio = 1, notte = 2.
    for l in range(lavoratori):
        total_shifts = sum(
            shifts[(l, g, MORNING)]
            + shifts[(l, g, AFTERNOON)]
            + 2 * shifts[(l, g, NIGHT)]
            for g in range(giorni)
        )
        model.add(total_shifts == SHIFTS_PER_MONTH)

    # Ogni lavoratore deve avere almeno un giorno libero a settimana.
    for l in range(lavoratori):
        for w in WEEKS:
            model.add(
                sum(shifts[(l, g, t)] for g in w for t in range(turni)) <= len(w) - 1
            )

    solver = cp_model.CpSolver()
    status = solver.solve(model)

    return status, solver, shifts
