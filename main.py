from SmartScheduler import worker_scheduling
from ortools.sat.python import cp_model

status, solver, shifts = worker_scheduling(
    lavoratori=10,
    giorni=31,
    turni=3
)

if status == cp_model.OPTIMAL:
    print("Soluzione ottima trovata")

elif status == cp_model.FEASIBLE:
    print("Soluzione ammissibile trovata")

elif status == cp_model.INFEASIBLE:
    print("Problema impossibile")

else:
    print("Nessuna soluzione")