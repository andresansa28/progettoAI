import collections
from datetime import date, timedelta
from ortools.sat.python import cp_model

# Simulazione modulo LLM_constraints se non presente
class LLM_constraints:
    UNAVAILABLE_DATES = {}

def add_staffing_constraints(model, shift_vars, num_workers, num_days, shifts):
    # Almeno 2 lavoratori per ogni turno ogni giorno
    for d in range(num_days):
        for s in shifts:
            model.Add(sum(shift_vars[(w, d, s)] for w in range(num_workers)) >= 2)
    
    # Max 1 turno al giorno per lavoratore
    for w in range(num_workers):
        for d in range(num_days):
            model.Add(sum(shift_vars[(w, d, s)] for s in shifts) <= 1)

def add_rest_constraints(model, shift_vars, num_workers, num_days, shifts):
    MORNING, AFTERNOON, NIGHT = shifts
    
    for w in range(num_workers):
        for d in range(num_days):
            # Regola Riposo Notturno: Se Notte al giorno d, riposo d+1 e d+2
            # Vincolo: Se lavora di notte al giorno d, non può lavorare in nessun turno in d+1 e d+2
            if d + 2 < num_days:
                model.Add(sum(shift_vars[(w, d, NIGHT)] + 
                              shift_vars[(w, d + 1, MORNING)] + shift_vars[(w, d + 1, AFTERNOON)] + shift_vars[(w, d + 1, NIGHT)] +
                              shift_vars[(w, d + 2, MORNING)] + shift_vars[(w, d + 2, AFTERNOON)] + shift_vars[(w, d + 2, NIGHT)]) <= 1)
            elif d + 1 < num_days:
                model.Add(sum(shift_vars[(w, d, NIGHT)] + 
                              shift_vars[(w, d + 1, MORNING)] + shift_vars[(w, d + 1, AFTERNOON)] + shift_vars[(w, d + 1, NIGHT)]) <= 1)

    # Riposo settimanale: Almeno un giorno libero in ogni finestra di 7 giorni
    for w in range(num_workers):
        for d in range(num_days - 6):
            model.Add(sum(shift_vars[(w, d + i, s)] for i in range(7) for s in shifts) >= 6)

def add_workload_constraints(model, shift_vars, num_workers, num_days, shifts):
    MORNING, AFTERNOON, NIGHT = shifts
    
    # Totale turni mese: 25 turni (Notte = 2, M/P = 1)
    for w in range(num_workers):
        model.Add(sum(shift_vars[(w, d, MORNING)] + shift_vars[(w, d, AFTERNOON)] + 2 * shift_vars[(w, d, NIGHT)] 
                      for d in range(num_days)) == 25)
    
    # Ore massime: 36h a settimana. 
    # Assumendo 6h per M/P e 12h per Notte. 36h = 6 turni M/P o 3 notti.
    # Finestra mobile di 7 giorni
    for w in range(num_workers):
        for d in range(num_days - 6):
            model.Add(sum(6 * (shift_vars[(w, d + i, MORNING)] + shift_vars[(w, d + i, AFTERNOON)]) + 
                          12 * shift_vars[(w, d + i, NIGHT)] for i in range(7)) <= 36)

def add_fairness_objective(model, shift_vars, num_workers, num_days, shifts, shift_mapping):
    worker_satisfaction = {}
    # Obiettivo: Bilanciare il carico totale tra i lavoratori
    total_workload = []
    for w in range(num_workers):
        w_load = sum(shift_vars[(w, d, shifts[0])] + shift_vars[(w, d, shifts[1])] + 2 * shift_vars[(w, d, shifts[2])] 
                     for d in range(num_days))
        total_workload.append(w_load)
    
    # Minimizzare la varianza del carico (semplificato con min-max)
    min_load = model.NewIntVar(0, 50, 'min_load')
    max_load = model.NewIntVar(0, 50, 'max_load')
    model.AddMinEquality(min_load, total_workload)
    model.AddMaxEquality(max_load, total_workload)
    model.Minimize(max_load - min_load)
    
    return worker_satisfaction

def solve_shift_scheduling():
    model = cp_model.CpModel()
    num_workers = 13
    num_days = 31
    MORNING, AFTERNOON, NIGHT = 0, 1, 2
    shifts = [MORNING, AFTERNOON, NIGHT]
    shift_mapping = {'MORNING': MORNING, 'AFTERNOON': AFTERNOON, 'NIGHT': NIGHT}
    start_date = date(2026, 12, 7)
    
    shift_vars = {}
    for w in range(num_workers):
        for d in range(num_days):
            for s in shifts:
                shift_vars[(w, d, s)] = model.NewBoolVar(f'shift_w{w}_d{d}_s{s}')
                
    add_staffing_constraints(model, shift_vars, num_workers, num_days, shifts)
    add_rest_constraints(model, shift_vars, num_workers, num_days, shifts)
    add_workload_constraints(model, shift_vars, num_workers, num_days, shifts)
    
    worker_satisfaction = add_fairness_objective(model, shift_vars, num_workers, num_days, shifts, shift_mapping)
                                                       
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.Solve(model)
    return status, solver, shift_vars, worker_satisfaction

if __name__ == '__main__':
    status, solver, shift_vars, worker_satisfaction = solve_shift_scheduling()
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Soluzione trovata con successo.")