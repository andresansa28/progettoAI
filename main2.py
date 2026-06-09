from ollama_parser import parse
from worker_agent import generate_constraints
from drafting_agent import generate_schedule_draft
from util import print_schedule_terminal
from hard_constraint_verifier import HardConstraintVerifier
import sys

def main():
    # file_txt_preferenze = "preferenze.txt"
    # parse(file_txt_preferenze)

    # file_json_preferenze = "preferences1.json"
    # generate_constraints(file_json_preferenze)

    # generate_schedule_draft()

    # #va a recuperare il file appena creato dalla funzione precedente
    # if 'schedule_draft_model' in sys.modules:
    #     del sys.modules['schedule_draft_model']
        
    try:
        import schedule_draft_model #anche se all'inizio segnale che il modulo non esiste, lanciate comunque il main che durante l'esecuizone il file si crea e poi lo importa in automatico
        
        
        print("\nEsecuzione della bozza LLM...")
        status, solver, shifts, worker_satisfaction = schedule_draft_model.solve_shift_scheduling()
        print(status)
        print_schedule_terminal(solver,shifts,13,31)
        verificatore = HardConstraintVerifier(solver, shifts, 13, 31, 3)
        print(verificatore.verify_all_constraints())
        
        
    except Exception as e:
        print(f"Errore critico di esecuzione del modello LLM: {e}")

main()



