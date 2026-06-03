def stampa_calendario(solver, shifts, lavoratori, giorni, turni):
    """
    Stampa il calendario in un formato tabellare pulito e leggibile.
    """
    # Mappiamo gli indici dei turni a nomi leggibili
    nomi_turni = {0: "Mattina", 1: "Pomeriggio", 2: "Notte"}
    
    print("\n" + "="*50)
    print("TABELLONE TURNI OSPEDALIERO")
    print("="*50)

    for g in range(giorni):
        print(f"\nGIORNO {g + 1}")
        print("-" * 30)
        
        for t in range(turni):
            assegnati = [
                f"L{l}" for l in range(lavoratori) 
                if solver.Value(shifts[(l, g, t)]) == 1
            ]
            
            nome_turno = nomi_turni.get(t, f"Turno {t}")
            lavoratori_str = ", ".join(assegnati) if assegnati else "Nessuno"
            
            print(f"  {nome_turno:<12} | {lavoratori_str}")
            
    print("\n" + "="*50)


