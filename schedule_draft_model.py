import collections
from datetime import date, timedelta
from ortools.sat.python import cp_model
import LLM_constraints

def add_staffing_constraints(model, shift_vars, num_workers, num_days, shifts):
    # Almeno 2 lavoratori per ogni turno in ogni giorno
    for d in range(num_days):
        for s in shifts:
            model.Add(sum(shift_vars[(w, d, s)] for w in range(num_workers)) >= 2)
    
    # Limite giornaliero: Max 1 turno al giorno per lavoratore
    for w in range(num_workers):
        for d in range(num_days):
            model.Add(sum(shift_vars[(w, d, s)] for s in shifts) <= 1)

def add_rest_constraints(model, shift_vars, num_workers, num_days, shifts):
    MORNING, AFTERNOON, NIGHT = shifts
    
    for w in range(num_workers):
        for d in range(num_days):
            # Regola Riposo Notturno: 2 giorni liberi consecutivi dopo ogni turno di notte
            if d + 1 < num_days:
                model.Add(sum(shift_vars[(w, d + 1, s)] for s in shifts) == 0).OnlyEnforceIf(shift_vars[(w, d, NIGHT)])
            if d + 2 < num_days:
                model.Add(sum(shift_vars[(w, d + 2, s)] for s in shifts) == 0).OnlyEnforceIf(shift_vars[(w, d, NIGHT)])
        
        # Riposo settimanale: Almeno un giorno di riposo in ogni finestra mobile di 7 giorni
        for d in range(num_days - 6):
            days_worked = []
            for i in range(7):
                is_working_day = model.NewBoolVar(f'work_w{w}_d{d+i}')
                model.Add(sum(shift_vars[(w, d + i, s)] for s in shifts) >= 1).OnlyEnforceIf(is_working_day)
                model.Add(sum(shift_vars[(w, d + i, s)] for s in shifts) == 0).OnlyEnforceIf(is_working_day.Not())
                days_worked.append(is_working_day)
            model.Add(sum(days_worked) <= 6)

def add_workload_constraints(model, shift_vars, num_workers, num_days, shifts):
    MORNING, AFTERNOON, NIGHT = shifts
    
    # Totale turni mese: 25 turni (Notte vale 2, altri valgono 1)
    for w in range(num_workers):
        total_load = sum(shift_vars[(w, d, MORNING)] + shift_vars[(w, d, AFTERNOON)] + 2 * shift_vars[(w, d, NIGHT)] 
                         for d in range(num_days))
        model.Add(total_load == 25)
        
    # Ore massime: 36 ore a settimana (Finestra mobile di 7 giorni)
    for w in range(num_workers):
        for d in range(num_days - 6):
            weekly_load = sum(shift_vars[(w, d + i, MORNING)] + 
                              shift_vars[(w, d + i, AFTERNOON)] + 
                              2 * shift_vars[(w, d + i, NIGHT)] 
                              for i in range(7))
            model.Add(weekly_load <= 6)

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
    
    # --- VINCOLI DI TOLLERANZA FAIRNESS SULLE PREFERENZE ---
    MIN_BOUNDS = {0: 50, 1: 55, 2: 55, 3: 45, 4: 40, 5: 40, 6: 40, 7: 40, 8: 40, 9: 65, 10: 55, 11: 45, 12: 55}
    
    for w_idx, min_score in MIN_BOUNDS.items():
        model.Add(worker_satisfaction[w_idx] >= min_score)
    
    return worker_satisfaction
                                                       
def solve_shift_scheduling():
    model = cp_model.CpModel()
    num_workers = 13
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