from SmartScheduler import worker_scheduling
from util import stampa_calendario
from ortools.sat.python import cp_model

status, solver, shifts = worker_scheduling(
    lavoratori=11,
    giorni=31,
    turni=3
)

if status == cp_model.OPTIMAL:
    print("Soluzione ottima trovata")
    #stampa_calendario(solver, shifts, 11, 31, 3)

elif status == cp_model.FEASIBLE:
    print("Soluzione ammissibile trovata")

elif status == cp_model.INFEASIBLE:
    print("Problema impossibile")

else:
    print("Nessuna soluzione")
