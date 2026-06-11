import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama


def generate_schedule_draft(violations=None):
    print("Avvio Drafting Agent")

    os.environ["GOOGLE_API_KEY"] = (
        "chiave"
    )

    try:
        #llm = ChatOllama(model="glm-4.7:cloud", temperature=0)
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            temperature=0,
        )
    except Exception as e:
        print(f"Errore nell'inizializzazione di Gemini: {e}")
        return

    # vincoli dettati dalla traccia, eventualemtne li mettiamo in un file a parte o laciamo cosi, vediamo
    hospital_rules = """
    REGOLE GENERALI (DA RISPETTARE TASSATIVAMENTE NELLA COSTRUZIONE DEL MODELLO):
    1. Orizzonte temporale: Dal 7 Dicembre 2026 al 6 Gennaio 2027 (31 giorni totali).
    2. Turni giornalieri: 3 turni. Mattina (8-14), Pomeriggio (14-20), Notte (20-8).
    3. Carico di lavoro: Mattina e Pomeriggio valgono 1 turno. La Notte vale come 2 turni (turno doppio).
    4. Ore massime: Nessun dipendente può superare le 36 ore a settimana.
    5. Totale turni mese: Ogni lavoratore deve coprire l'equivalente di 25 turni in un mese.
    6. Regola Riposo Notturno: È obbligatorio garantire a ciascun dipendente DUE giorni liberi consecutivi dopo ogni turno di notte.
    7. Limite giornaliero: Max 1 turno al giorno per lavoratore
    8. Riposo settimanale: Almeno un giorno di riposo garantito a settimana (finestra mobile di 7 giorni).
    
    SCENARIO A (Livelli minimi di personale):
    - Ci sono 13 lavoratori in totale, indici da 0 a 12.
    - Almeno 2 lavoratori devono essere assegnati a ogni turno.
    """
    violations_list = ""

    if violations:
        violations_list = f"""
    ATTENZIONE: IL MODELLO PRECEDENTE NON ERA VALIDO.

    VINCOLI HARD VIOLATI:

    {chr(10).join("- " + v for v in violations)}

    Devi correggere esplicitamente questi errori.
    Prima di generare il codice, analizza le cause delle violazioni e rafforza i vincoli OR-Tools necessari affinché non possano più verificarsi.
    """

    prompt_template = ChatPromptTemplate.from_template("""
Sei un Senior Python Engineer specializzato in Google OR-Tools (CP-SAT Solver).
Devi generare uno script Python eseguibile che produca un calendario ospedaliero bilanciato.

REGOLE E VINCOLI HARD DELL'OSPEDALE (IL TESTO LUNGO):
{hospital_rules}
VIOLAZIONI DEL MODELLO RECENTE (SE PRESENTI)
{violations_list}


IL TUO OBIETTIVO CHIAVE:
Generare un codice Python completo che utilizza `cp_model`. Per evitare bug e mantenere il codice scalabile, devi obbligatoriamente organizzare i vincoli all'interno delle funzioni modulari che trovi nello scheletro qui sotto.

ISTRUZIONI DI COMPILAZIONE PER OGNI FUNZIONE:
1. Dentro 'add_staffing_constraints': Scrivi la logica OR-Tools per coprire il personale minimo per ogni turno.
2. Dentro 'add_rest_constraints': Scrivi i vincoli sui riposi giornalieri, riposi post-notte e riposi settimanali.
3. Dentro 'add_workload_constraints': Scrivi i limiti sulle ore massime settimanali (36h) e il totale dei turni mensili (25 turni).
4. Dentro 'add_fairness_objective': Implementa la funzione obiettivo Max-Min Fairness usando il dizionario delle preferenze.

STRUTTURA OBBLIGATORIA DEL CODICE (LO SCHELETRO MODULARE):
Genera SOLO codice Python valido. Riempi i corpi delle funzioni sostituendo i vari 'pass' con il codice matematico corretto. Non modificare l'orchestratore principale `solve_shift_scheduling`.
NON AGGIUNGERE NESSUNA SCRITTA ALL'INZIO DEL FILE

```python
import collections
from datetime import date, timedelta
from ortools.sat.python import cp_model
import LLM_constraints

def add_staffing_constraints(model, shift_vars, num_workers, num_days, shifts):
    pass

def add_rest_constraints(model, shift_vars, num_workers, num_days, shifts):
    
    pass

def add_workload_constraints(model, shift_vars, num_workers, num_days, shifts):
   
    pass

def add_fairness_objective(model, shift_vars, num_workers, num_days, shifts, shift_mapping):
    
    worker_satisfaction = {{}}
    return worker_satisfaction

def solve_shift_scheduling():
    model = cp_model.CpModel()
    num_workers = 13
    num_days = 31
    MORNING = 0
    AFTERNOON = 1
    NIGHT = 2
    shifts = [MORNING, AFTERNOON, NIGHT]
    shift_mapping = {{'MORNING': MORNING, 'AFTERNOON': AFTERNOON, 'NIGHT': NIGHT}}
    start_date = date(2026, 12, 7)
    
    shift_vars = {{}}
    for w in range(num_workers):
        for d in range(num_days):
            for s in shifts:
                shift_vars[(w, d, s)] = model.NewBoolVar(f'shift_w{{w}}_d{{d}}_s{{s}}')
                
    # Invocazioni automatiche dei moduli
    add_staffing_constraints(model, shift_vars, num_workers, num_days, shifts)
    add_rest_constraints(model, shift_vars, num_workers, num_days, shifts)
    add_workload_constraints(model, shift_vars, num_workers, num_days, shifts)
    
    # Vincoli indisponibilità
    if hasattr(LLM_constraints, 'UNAVAILABLE_DATES'):
        for w, dates_list in LLM_constraints.UNAVAILABLE_DATES.items():
            for date_str in dates_list:
                try:
                    y, m, d_val = map(int, date_str.split('-'))
                    d_idx = (date(y, m, d_val) - start_date).days
                    if 0 <= d_idx < num_days:
                        for s in shifts:
                            model.Add(shift_vars[(w, d_idx, s)] == 0)
                except Exception:
                    pass
    
    worker_satisfaction = add_fairness_objective(model, shift_vars, num_workers, num_days, shifts, shift_mapping)
                                                       
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.Solve(model)
    return status, solver, shift_vars, worker_satisfaction

if __name__ == '__main__':
    status, solver, shift_vars, worker_satisfaction = solve_shift_scheduling()

""")
    print("Invocazione di Gemini 3.5 Flash")

    try:  # questo try serve per formattare pe rbene la risposta generata da gemini altrimenti può contenere altre info inutli
        parser = StrOutputParser()
        chain = prompt_template | llm | parser

        risultato_grezzo = chain.invoke({"hospital_rules": hospital_rules, "violations_list": violations_list})

        codice_pulito = (
            risultato_grezzo.replace("```python\n", "")
            .replace("```python", "")
            .replace("```", "")
            .strip()
        )

        output_filename = "schedule_draft_model.py"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(codice_pulito)

        print(
            f"SUCCESSO! Il file '{output_filename}' è stato generato e contiene la bozza del calendario."
        )

    except Exception as e:
        print(f"ERRORE durante la generazione: {e}")


if __name__ == "__main__":
    generate_schedule_draft()
