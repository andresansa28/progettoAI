from SmartScheduler import worker_scheduling
from excel_calendar import export_schedule_to_excel
from hard_constaint_verifier import HardConstraintVerifier
from ortools.sat.python import cp_model
from fairness import calcola_fairness

LAVORATORI = 13
GIORNI = 31 
TURNI = 3

status, solver, shifts,termini_obiettivo = worker_scheduling(
    lavoratori=LAVORATORI,
    giorni=GIORNI,
    turni=TURNI
)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("Soluzione ottima/fattibile trovata:")
    output_path = export_schedule_to_excel(solver, shifts, LAVORATORI, GIORNI, TURNI)
    print(f"Calendario Excel creato: {output_path}")
    verifier = HardConstraintVerifier(solver, shifts, LAVORATORI, GIORNI, TURNI)
    violazioni = verifier.verify_all_constraints()
    print(violazioni)
    print(calcola_fairness(solver,termini_obiettivo,LAVORATORI))

elif status == cp_model.INFEASIBLE:
    print("Problema impossibile")

else:
    print("Nessuna soluzione")
