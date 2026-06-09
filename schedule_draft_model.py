import collections
from datetime import date, timedelta
from ortools.sat.python import cp_model
import LLM_constraints

def solve_shift_scheduling():
    model = cp_model.CpModel()
    
    # 1. DEFINIZIONE DATI E VARIABILI
    num_workers = 13
    num_days = 31
    shifts = ['MORNING', 'AFTERNOON', 'NIGHT']
    
    start_date = date(2026, 12, 7)
    
    # shift_vars[(w, d, s)]
    shift_vars = {}
    for w in range(num_workers):
        for d in range(num_days):
            for s in shifts:
                shift_vars[(w, d, s)] = model.NewBoolVar(f'shift_w{w}_d{d}_s{s}')
                
    # 2. VINCOLI HARD DELL'OSPEDALE (Staffing, Limiti legali, Riposi post-notte)
    
    # Vincolo: Almeno 2 lavoratori assegnati a ogni turno (Scenario A)
    for d in range(num_days):
        for s in shifts:
            model.Add(sum(shift_vars[(w, d, s)] for w in range(num_workers)) >= 2)
            
    # Vincolo: Max 1 turno al giorno per lavoratore
    for w in range(num_workers):
        for d in range(num_days):
            model.Add(sum(shift_vars[(w, d, s)] for s in shifts) <= 1)
            
    # Vincolo: Ore massime (Nessun dipendente può superare le 36 ore a settimana - finestra mobile di 7 giorni)
    # Mattina = 6 ore, Pomeriggio = 6 ore, Notte = 12 ore
    for w in range(num_workers):
        for d in range(num_days - 6):
            model.Add(
                sum(
                    6 * shift_vars[(w, d + i, 'MORNING')] +
                    6 * shift_vars[(w, d + i, 'AFTERNOON')] +
                    12 * shift_vars[(w, d + i, 'NIGHT')]
                    for i in range(7)
                ) <= 36
            )
            
    # Vincolo: Totale turni mese (Ogni lavoratore deve coprire l'equivalente di 25 turni)
    # Mattina/Pomeriggio = 1 turno, Notte = 2 turni
    for w in range(num_workers):
        model.Add(
            sum(
                shift_vars[(w, d, 'MORNING')] +
                shift_vars[(w, d, 'AFTERNOON')] +
                2 * shift_vars[(w, d, 'NIGHT')]
                for d in range(num_days)
            ) == 25
        )
        
    # Vincolo: Regola Riposo Notturno (DUE giorni liberi consecutivi dopo ogni turno di notte)
    for w in range(num_workers):
        for d in range(num_days):
            if d + 1 < num_days:
                for s in shifts:
                    model.Add(shift_vars[(w, d, 'NIGHT')] + shift_vars[(w, d + 1, s)] <= 1)
            if d + 2 < num_days:
                for s in shifts:
                    model.Add(shift_vars[(w, d, 'NIGHT')] + shift_vars[(w, d + 2, s)] <= 1)
                    
    # Vincolo: Nessun turno consecutivo tra giorni adiacenti (es. Pomeriggio e poi Mattina seguente)
    # Nota: Notte e poi Mattina/Pomeriggio seguente è già coperto dal riposo notturno di 2 giorni.
    for w in range(num_workers):
        for d in range(num_days - 1):
            model.Add(shift_vars[(w, d, 'AFTERNOON')] + shift_vars[(w, d + 1, 'MORNING')] <= 1)
            
    # Vincolo: Riposo settimanale (Almeno un giorno di riposo garantito a settimana - finestra mobile di 7 giorni)
    for w in range(num_workers):
        for d in range(num_days - 6):
            model.Add(sum(shift_vars[(w, d + i, s)] for i in range(7) for s in shifts) <= 6)
    
    # 3. INTEGRAZIONE PREFERENZE (UNAVAILABLE_DATES)
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
    
    # 4. FUNZIONE OBIETTIVO E FAIRNESS (Max-Min Fairness)
    def get_day_index(date_str):
        try:
            y, m, d_val = map(int, date_str.split('-'))
            d_idx = (date(y, m, d_val) - start_date).days
            if 0 <= d_idx < num_days:
                return d_idx
        except Exception:
            pass
        return None

    worker_satisfaction = {}
    for w in range(num_workers):
        sat_expr = []
        
        # Preferred shifts (+10)
        if hasattr(LLM_constraints, 'PREFERRED_SHIFTS') and LLM_constraints.PREFERRED_SHIFTS:
            prefs = LLM_constraints.PREFERRED_SHIFTS.get(w, [])
            for item in prefs:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    date_str, s = item
                    d_idx = get_day_index(date_str)
                    if d_idx is not None and s in shifts:
                        sat_expr.append(10 * shift_vars[(w, d_idx, s)])
                        
        # Preferred days off (+10)
        if hasattr(LLM_constraints, 'PREFERRED_DAYS_OFF') and LLM_constraints.PREFERRED_DAYS_OFF:
            days_off = LLM_constraints.PREFERRED_DAYS_OFF.get(w, [])
            for date_str in days_off:
                d_idx = get_day_index(date_str)
                if d_idx is not None:
                    day_off_var = model.NewBoolVar(f'day_off_w{w}_d{d_idx}')
                    model.Add(day_off_var == 1 - sum(shift_vars[(w, d_idx, s)] for s in shifts))
                    sat_expr.append(10 * day_off_var)
                    
        # Disliked shifts (-10)
        if hasattr(LLM_constraints, 'DISLIKED_SHIFTS') and LLM_constraints.DISLIKED_SHIFTS:
            dislikes = LLM_constraints.DISLIKED_SHIFTS.get(w, [])
            for item in dislikes:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    date_str, s = item
                    d_idx = get_day_index(date_str)
                    if d_idx is not None and s in shifts:
                        sat_expr.append(-10 * shift_vars[(w, d_idx, s)])
                        
        # Create satisfaction variable for worker w
        sat_var = model.NewIntVar(-1000, 1000, f'sat_w{w}')
        if sat_expr:
            model.Add(sat_var == sum(sat_expr))
        else:
            model.Add(sat_var == 0)
        worker_satisfaction[w] = sat_var
        
    # Max-Min Fairness: massimizzare la soddisfazione minima tra tutti i lavoratori
    min_sat = model.NewIntVar(-1000, 1000, 'min_sat')
    for w in range(num_workers):
        model.Add(min_sat <= worker_satisfaction[w])
        
    # Obiettivo combinato: massimizzare la soddisfazione minima (priorità alta) 
    # e la somma totale delle soddisfazioni (priorità bassa per evitare inefficienze paretiane)
    model.Maximize(10000 * min_sat + sum(worker_satisfaction[w] for w in range(num_workers)))
                                                       
    # 5. RISOLUZIONE E OUTPUT (NON MODIFICARE QUESTA SEZIONE)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.Solve(model)
    
    # Restituisce gli oggetti grezzi per permettere alla Fase 3 e 4 di manipolarli
    return status, solver, shift_vars, worker_satisfaction

if __name__ == '__main__':
    status, solver, shift_vars, worker_satisfaction = solve_shift_scheduling()