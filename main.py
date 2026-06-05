from SmartScheduler import worker_scheduling
from excel_calendar import export_schedule_to_excel
from ortools.sat.python import cp_model

status, solver, shifts = worker_scheduling(
    lavoratori=13,
    giorni=31,
    turni=3
)

if status == cp_model.OPTIMAL:
    print("Soluzione ottima trovata")
    output_path = export_schedule_to_excel(solver, shifts, 13, 31, 3)
    print(f"Calendario Excel creato: {output_path}")

elif status == cp_model.FEASIBLE:
    print("Soluzione ammissibile trovata")
    output_path = export_schedule_to_excel(solver, shifts, 13, 31, 3)
    print(f"Calendario Excel creato: {output_path}")

elif status == cp_model.INFEASIBLE:
    print("Problema impossibile")

else:
    print("Nessuna soluzione")
