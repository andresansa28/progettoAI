from datetime import date, timedelta

def print_schedule_terminal(solver, shifts, lavoratori, giorni):
    """
    Stampa il calendario in formato tabellare nel terminale.
    Richiede gli oggetti solver e shifts restituiti da OR-Tools.
    """
    MORNING = 0
    AFTERNOON = 1
    NIGHT = 2
    
    start_date = date(2026, 12, 7)
    
    print("\n" + "="*88)
    print(" CALENDARIO OSPEDALIERO (7 Dic. 2026 - 6 Gen. 2027) ".center(88))
    print("="*88 + "\n")
    
    # --- 1. Costruzione dell'intestazione (Giorni del mese) ---
    header = f"{'Lav/Gio ':<9}|"
    for g in range(giorni):
        current_date = start_date + timedelta(days=g)
        header += f" {current_date.strftime('%d')}"
    header += " | Ore | TurniEq"
    
    print(header)
    print("-" * len(header))
    
    for l in range(lavoratori):
        row_str = f"Worker {l:<2} |"
        ore_totali = 0
        turni_eq = 0
        
        for g in range(giorni):
            assigned_shift = "-"  # Default: giorno libero
            
            if solver.Value(shifts[(l, g, MORNING)]) == 1:
                assigned_shift = "M"
                ore_totali += 6
                turni_eq += 1
            elif solver.Value(shifts[(l, g, AFTERNOON)]) == 1:
                assigned_shift = "A"
                ore_totali += 6
                turni_eq += 1
            elif solver.Value(shifts[(l, g, NIGHT)]) == 1:
                assigned_shift = "N"
                ore_totali += 12
                turni_eq += 2
                
            row_str += f" {assigned_shift:>2}"
            
        row_str += f" | {ore_totali:>3} | {turni_eq:>7}"
        print(row_str)
        
    print("-" * len(header) + "\n")