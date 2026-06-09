import LLM_constraints #se da errore all'inizio è eprche il file ancora non esiste ma dop l'agente lo genreea (sio speera)
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
            date_str = current_date.strftime("%Y-%m-%d")
            day_name = current_date.strftime("%A").upper()
            
            lavorato_oggi = False
            for t in range(3):
                if solver.Value(shifts[(w, g, t)]) == 1:
                    # Crea la tupla (data, tipo_turno) come richiesto da LLM_constraints
                    assigned_shifts_list.append((date_str, shift_names[t]))
                    lavorato_oggi = True
            
            if not lavorato_oggi:
                assigned_days_off_list.append(day_name)
                
       #Funzione pres a da LLm costraint che genera l'agente nella fase 2, serve appunto per calcoalre il punteggio di ognoi lavoratore in base
       #ai punti che assegna lui nel codice quando lo genrea
        score = LLM_constraints.evaluate_worker_satisfaction(w, assigned_shifts_list, assigned_days_off_list)
        fairness_dict[w] = score
        
    return fairness_dict