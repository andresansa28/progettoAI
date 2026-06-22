import collections
from datetime import date, timedelta
from ortools.sat.python import cp_model
import LLM_constraints

def add_staffing_constraints(model, shift_vars, num_workers, num_days, shifts):
    # Standard: 0-12, Specializzati: 13-18
    standard_workers = range(13)
    specialized_workers = range(13, 19)
    
    for d in range(num_days):
        for s in shifts:
            # Almeno 2 standard + 1 specializzato (i specializzati possono fare da standard)
            # Totale minimo 3 persone per turno
            model.Add(sum(shift_vars[(w, d, s)] for w in range(num_workers)) >= 3)
            # Almeno 1 specializzato
            model.Add(sum(shift_vars[(w, d, s)] for w in specialized_workers) >= 1)
            # Almeno 2 standard (inclusi i specializzati che contano come standard)
            model.Add(sum(shift_vars[(w, d, s)] for w in range(num_workers)) >= 3)

def add_rest_constraints(model, shift_vars, num_workers, num_days, shifts):
    for w in range(num_workers):
        for d in range(num_days):
            # Max 1 turno al giorno
            model.Add(sum(shift_vars[(w, d, s)] for s in shifts) <= 1)
            
            # Regola Riposo Notturno: Se notte al giorno d, liberi d+1 e d+2
            if d < num_days - 2:
                model.Add(sum(shift_vars[(w, d, 2)] for s in shifts) == 1).OnlyEnforceIf(
                    [shift_vars[(w, d+1, s)].Not() for s in shifts] + 
                    [shift_vars[(w, d+2, s)].Not() for s in shifts]
                )
        
        # Riposo settimanale: almeno 1 giorno libero ogni 7 giorni
        for d in range(num_days - 6):
            model.Add(sum(shift_vars[(w, d + i, s)] for i in range(7) for s in shifts) <= 6)

def add_workload_constraints(model, shift_vars, num_workers, num_days, shifts):
    # Carico: Mattina/Pomeriggio = 1, Notte = 2
    # Totale 25 turni al mese
    for w in range(num_workers):
        total_load = []
        for d in range(num_days):
            total_load.append(shift_vars[(w, d, 0)] * 1) # Mattina
            total_load.append(shift_vars[(w, d, 1)] * 1) # Pomeriggio
            total_load.append(shift_vars[(w, d, 2)] * 2) # Notte
        
        model.Add(sum(total_load) == 25)
        
        # Ore massime: 36h a settimana. 
        # Assumendo 6h per turno (M/P) e 12h per notte.
        # In 7 giorni, max 36 ore.
        for d in range(num_days - 6):
            weekly_load = []
            for i in range(7):
                weekly_load.append(shift_vars[(w, d + i, 0)] * 6)
                weekly_load.append(shift_vars[(w, d + i, 1)] * 6)
                weekly_load.append(shift_vars[(w, d + i, 2)] * 12)
            model.Add(sum(weekly_load) <= 36)

def add_fairness_objective(model, shift_vars, num_workers, num_days, shifts, shift_mapping):
    worker_satisfaction = {}
    start_date = date(2026, 12, 7)
    shift_names = {0: "MORNING", 1: "AFTERNOON", 2: "NIGHT"}
    
    for w in range(num_workers):
        score_expr = 0
        if hasattr(LLM_constraints, 'WORKER_PREFS') and w in LLM_constraints.WORKER_PREFS:
            prefs = LLM_constraints.WORKER_PREFS[w]
            for d in range(num_days):
                curr_date = start_date + timedelta(days=d)
                day_name = curr_date.strftime("%A").upper()
                for s in shifts:
                    if shift_names[s] == prefs.get("shift"):
                        score_expr += shift_vars[(w, d, s)] * getattr(LLM_constraints, 'BONUS_PREFERRED_SHIFT', 5)
                    if shift_names[s] in prefs.get("disliked", []):
                        score_expr += shift_vars[(w, d, s)] * getattr(LLM_constraints, 'PENALTY_DISLIKED_SHIFT', -10)
                
                if day_name == prefs.get("day_off"):
                    works_that_day = sum(shift_vars[(w, d, s)] for s in shifts)
                    is_off = model.NewBoolVar(f'is_off_{w}_{d}')
                    model.Add(works_that_day == 0).OnlyEnforceIf(is_off)
                    model.Add(works_that_day > 0).OnlyEnforceIf(is_off.Not())
                    score_expr += is_off * getattr(LLM_constraints, 'BONUS_DAY_OFF', 10)
                    
        sat_var = model.NewIntVar(-1000, 1000, f'sat_w_{w}')
        model.Add(sat_var == score_expr)
        worker_satisfaction[w] = sat_var
        
    min_sat = model.NewIntVar(-1000, 1000, 'min_sat')
    model.AddMinEquality(min_sat, [worker_satisfaction[w] for w in range(num_workers)])
    model.Maximize(min_sat)
    
    return worker_satisfaction
                                                       
def solve_shift_scheduling():
    model = cp_model.CpModel()
    num_workers = 19
    num_days = 31
    MORNING = 0
    AFTERNOON = 1
    NIGHT = 2
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
    
    if hasattr(LLM_constraints, 'UNAVAILABLE_DATES'):
        for w, dates_list in LLM_constraints.UNAVAILABLE_DATES.items():
            for date_str in dates_list:
                try:
                    y, m, d_val = map(int, date_str.split('-'))
                    d_idx = (date(y, m, d_val) - start_date).days
                    if 0 <= d_idx < num_days:
                        for s in shifts:
                            model.Add(shift_vars[(w, d_idx, s)] == 0)
                except Exception:
                    pass
    
    worker_satisfaction = add_fairness_objective(model, shift_vars, num_workers, num_days, shifts, shift_mapping)
                                                       
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.Solve(model)
    return status, solver, shift_vars, worker_satisfaction

if __name__ == '__main__':
    status, solver, shift_vars, worker_satisfaction = solve_shift_scheduling()