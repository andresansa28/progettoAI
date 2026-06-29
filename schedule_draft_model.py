import collections
from datetime import date, timedelta
from ortools.sat.python import cp_model
import LLM_constraints

def add_staffing_constraints(model, shift_vars, num_workers, num_days, shifts):
    # 19 lavoratori: 0-12 standard, 13-18 specializzati
    specialized_workers = range(13, 19)
    
    for d in range(num_days):
        for s in shifts:
            # Totale lavoratori per turno >= 3
            model.Add(sum(shift_vars[(w, d, s)] for w in range(num_workers)) >= 3)
            # Almeno 1 specializzato per turno
            model.Add(sum(shift_vars[(w, d, s)] for w in specialized_workers) >= 1)

def add_rest_constraints(model, shift_vars, num_workers, num_days, shifts):
    MORNING, AFTERNOON, NIGHT = shifts
    
    for w in range(num_workers):
        for d in range(num_days):
            # Limite giornaliero: Max 1 turno al giorno
            model.Add(sum(shift_vars[(w, d, s)] for s in shifts) <= 1)
            
            # Regola Riposo Notturno: Se notte oggi, allora turni domani = 0 e dopodomani = 0
            if d + 2 < num_days:
                model.Add(sum(shift_vars[(w, d + 1, s)] for s in shifts) == 0).OnlyEnforceIf(shift_vars[(w, d, NIGHT)])
                model.Add(sum(shift_vars[(w, d + 2, s)] for s in shifts) == 0).OnlyEnforceIf(shift_vars[(w, d, NIGHT)])
            elif d + 1 < num_days:
                model.Add(sum(shift_vars[(w, d + 1, s)] for s in shifts) == 0).OnlyEnforceIf(shift_vars[(w, d, NIGHT)])

        # Riposo settimanale: Almeno 1 giorno libero per ogni blocco di 7 giorni
        for start_block in range(0, num_days, 7):
            end_block = min(start_block + 7, num_days)
            # Somma dei giorni lavorati nel blocco
            days_worked = []
            for d in range(start_block, end_block):
                is_working = model.NewBoolVar(f'work_{w}_{d}')
                model.Add(is_working == sum(shift_vars[(w, d, s)] for s in shifts))
                days_worked.append(is_working)
            
            # Almeno un giorno libero (somma dei lavorati <= lunghezza_blocco - 1)
            model.Add(sum(days_worked) <= (end_block - start_block) - 1)

def add_workload_constraints(model, shift_vars, num_workers, num_days, shifts):
    MORNING, AFTERNOON, NIGHT = shifts
    
    for w in range(num_workers):
        # Totale turni mese == 25 (Notte = 2, altri = 1)
        total_load = sum(
            shift_vars[(w, d, MORNING)] * 1 + 
            shift_vars[(w, d, AFTERNOON)] * 1 + 
            shift_vars[(w, d, NIGHT)] * 2 
            for d in range(num_days)
        )
        model.Add(total_load == 25)
        
        # Ore massime: Max 6 turni equivalenti per blocco di 7 giorni
        for start_block in range(0, num_days, 7):
            end_block = min(start_block + 7, num_days)
            weekly_load = sum(
                shift_vars[(w, d, MORNING)] * 1 + 
                shift_vars[(w, d, AFTERNOON)] * 1 + 
                shift_vars[(w, d, NIGHT)] * 2 
                for d in range(start_block, end_block)
            )
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
        
    # --- VINCOLI DI TOLLERANZA FAIRNESS SULLE PREFERENZE ---
    MIN_BOUNDS = {0: 60, 1: 40, 2: 45, 3: 50, 4: 30, 5: 35, 6: 40, 7: 40, 8: 30, 9: 55, 10: 45, 11: 30, 12: 55, 13: 35, 14: 30, 15: 35, 16: 30, 17: 35, 18: 30}
    
    for w_idx, min_score in MIN_BOUNDS.items():
        model.Add(worker_satisfaction[w_idx] >= min_score)
        
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