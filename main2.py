from ollama_parser import parse
from worker_agent import generate_constraints
from drafting_agent import generate_schedule_draft
from util import print_schedule_terminal
from hard_constraint_verifier import HardConstraintVerifier
import sys


MAX_ATTEMPTS = 5

def main():
    # file_txt_preferenze = "preferenze.txt"
    # parse(file_txt_preferenze)

    file_json_preferenze = "preferences1.json"
    generate_constraints(file_json_preferenze)

    generate_schedule_draft()  # una sola volta all'inizio


    attempt = 0

    while attempt < MAX_ATTEMPTS:

        if "schedule_draft_model" in sys.modules:
            del sys.modules["schedule_draft_model"]

        import schedule_draft_model
        import importlib

        importlib.reload(schedule_draft_model)

        status, solver, shifts, worker_satisfaction = (
            schedule_draft_model.solve_shift_scheduling()
        )
        print(status)

        verificatore = HardConstraintVerifier(solver, shifts, 13, 31, 3)

        violations = verificatore.verify_all_constraints()

        if not violations:

            print("Tutti i vincoli HARD sono rispettati!")
            print_schedule_terminal(solver, shifts, 13, 31)
            break

        print("Violazioni rilevate:")
        for v in violations:
            print(v)

        attempt += 1

        print(f"\nRigenerazione modello - tentativo {attempt}")

        generate_schedule_draft(violations)
            
    else:
            print("Numero massimo di tentativi raggiunto.")
main()
