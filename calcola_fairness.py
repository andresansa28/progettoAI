import LLM_constraints 
from datetime import date, timedelta

def calcola_fairness_dizionario(solver, shifts, num_workers, num_days):
    start_date = date(2026, 12, 7)
    shift_names = {0: "MORNING", 1: "AFTERNOON", 2: "NIGHT"}
    
    fairness_dict = {}
    
    for w in range(num_workers):
        assigned_shifts_list = []
        assigned_days_off_list = []
        
        for g in range(num_days):
            current_date = start_date + timedelta(days=g)
            day_name = current_date.strftime("%A").upper()
            
            lavorato_oggi = False
            for t in range(3):
                # Se il modello va in eccezione qui, significa che è INFEASIBLE
                if solver.Value(shifts[(w, g, t)]) == 1:
                    # PASSIAMO LA STRINGA ESATTA, COSÌ LLM_CONSTRAINTS LA LEGGE BENE
                    assigned_shifts_list.append(shift_names[t])
                    lavorato_oggi = True
            
            if not lavorato_oggi:
                assigned_days_off_list.append(day_name)
                
        score = LLM_constraints.evaluate_worker_satisfaction(w, assigned_shifts_list, assigned_days_off_list)
        fairness_dict[w] = score
        
    return fairness_dict