from ortools.sat.python import cp_model
from config import *


def worker_scheduling(lavoratori, giorni, turni):
    model = cp_model.CpModel()

    shifts = {}

    # Per codificare la "griglia" sulla quale posizionare i turni creiamo un dizionario
    # dove ogni entry (i, g, t) è pari ad 1 se il lavoratore w è di servizio nel giorno g al turno t
    for l in range(lavoratori):
        for g in range(giorni):
            for t in range(turni):
                shifts[(l, g, t)] = model.new_bool_var(f"l{l}_g{g}_t{t}")

    # Un infermiere per turno
    for g in range(giorni):
        for t in range(turni):
            model.add(
                sum(shifts[(l, g, t)] for l in range(lavoratori))
                >= MIN_WORKERS_PER_SHIFT
            )

    # Un turno per giorno per ciascun infermiere
    for l in range(lavoratori):
        for g in range(giorni):
            model.add_at_most_one([shifts[(l, g, t)] for t in range(turni)])

    # Ogni lavoratore dopo una notte deve riposare due giorni
    for l in range(lavoratori):
        for g in range(
            giorni - 2
        ):  # inserisco -2 perché altrimenti andrei a cercare di accedere a giorni che non esistono
            model.add(
                shifts[(l, g, NIGHT)]
                + sum(shifts[(l, g + 1, t)] for t in range(turni))
                + sum(shifts[(l, g + 2, t)] for t in range(turni))
                <= 1
            )

    # Ogni lavoratore non deve superare le 36 ore settimanali
    for l in range(lavoratori):
        for w in WEEKS:
            model.add(
                sum(
                    shifts[(l, g, t)]
                    * SHIFT_HOURS[t]  # il valore è 6 per mattina e pome, 12 per notte
                    for g in w
                    for t in range(turni)
                )
                <= MAX_HOURS_PER_WEEK
            )

    # Ogni lavoratore deve fare almeno 25 turni al mese
    # La notte vale come 2 turni, quindi moltiplichiamo per 2 i turni notturni
    # for l in range(lavoratori):

    #     total_shifts = sum(
    #         shifts[(l, g, MORNING)]
    #         + shifts[(l, g, AFTERNOON)]
    #         + 2 * shifts[(l, g, NIGHT)]
    #         for g in range(giorni)
    #     )
    #     model.add(total_shifts == SHIFTS_PER_MONTH)

    # ogni lavoratore deve avere almeno un giorno libero a settimana
    # il metodo viene cosi implementato perchè ogni lavoratore può fare max un turno al giorno
    # con almeno un giorno libero a settimana, il lavoratore non può fare più di 6 turni a settimana
    # la somma allora sarà al massimo 6
    for l in range(lavoratori):
        for w in WEEKS:
            model.add(
                sum(shifts[(l, g, t)] for g in w for t in range(turni)) <= len(w) - 1
            )

    solver = cp_model.CpSolver()
    status = solver.solve(model)

    return status, solver, shifts
