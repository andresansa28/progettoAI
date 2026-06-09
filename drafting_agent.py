import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def generate_schedule_draft(violations=None):
    print("Avvio Drafting Agent")

    os.environ["GOOGLE_API_KEY"] = (
        "chiave_api"
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
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
    7. Limite giornaliero: Max 1 turno al giorno per lavoratore, e nessun turno consecutivo tra giorni adiacenti (es. Notte e poi Mattina seguente, oppure Pomeriggio e poi Mattina seguente).
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

REGOLE E VINCOLI HARD DELL'OSPEDALE:
{hospital_rules}

VIOLAZIONI RILEVATE NEL MODELLO PRECEDENTE (se presenti):
{violations_list}

Assumi che esista un modulo chiamato `LLM_constraints.py` nella stessa directory.
Questo modulo contiene le seguenti variabili: `UNAVAILABLE_DATES` (dizionario con liste di stringhe come "YYYY-MM-DD"), `PREFERRED_SHIFTS`, `PREFERRED_DAYS_OFF`, `DISLIKED_SHIFTS` e la funzione `evaluate_worker_satisfaction(worker_id, assigned_shifts_list, assigned_days_off_list)`.

IL TUO OBIETTIVO:
Generare un codice Python completo che utilizza `cp_model` di `ortools.sat.python`.
Il sistema deve implementare la logica Max-Min Fairness per distribuire equamente la soddisfazione.

STRUTTURA OBBLIGATORIA DEL CODICE GENERATO:
Genera SOLO codice Python valido. Usa lo scheletro esatto fornito qui sotto e riempi solo le parti mancanti (i VINCOLI HARD e la FUNZIONE OBIETTIVO). Non modificare le parti già scritte nello scheletro, poiché contengono i fix per il parsing delle date e l'output.
NON GENERARE QUESTA RIGA ALL'INZIO:Ecco lo script Python completo e pronto all'uso, strutturato secondo le tue specifiche e pronto per essere integrato con il modulo `LLM_constraints.py`.
```python
import collections
from datetime import date, timedelta
from ortools.sat.python import cp_model
import LLM_constraints

def solve_shift_scheduling():
    model = cp_model.CpModel()
    
    # 1. DEFINIZIONE DATI E VARIABILI
    num_workers = 13
    num_days = 31
    shifts = ['MORNING', 'AFTERNOON', 'NIGHT']
    
    start_date = date(2026, 12, 7)
    
    # shift_vars[(w, d, s)]
    shift_vars = {{}}
    for w in range(num_workers):
        for d in range(num_days):
            for s in range(len(shifts)):
                shift_vars[(w, d, s)] = model.NewBoolVar(f'shift_w{{w}}_d{{d}}_s{{s}}')
                
    # 2. VINCOLI HARD DELL'OSPEDALE (Staffing, Limiti legali, Riposi post-notte)
    # [IMPLEMENTA QUI TUTTI I 7 VINCOLI HARD DESCRITTI NELLE REGOLE]
    
    # 3. INTEGRAZIONE PREFERENZE (UNAVAILABLE_DATES)
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
    
    # 4. FUNZIONE OBIETTIVO E FAIRNESS (Max-Min Fairness)
    # [IMPLEMENTA LA LOGICA DELLA FUNZIONE OBIETTIVO LEGGENDO PREFERRED_SHIFTS, PREFERRED_DAYS_OFF, DISLIKED_SHIFTS da LLM_constraints]
    # ATTENZIONE: Devi obbligatoriamente salvare la variabile di soddisfazione di ogni singolo lavoratore in un dizionario o lista chiamato `worker_satisfaction` (es. worker_satisfaction[w] = sat_var).
                                                       
    # 5. RISOLUZIONE E OUTPUT (NON MODIFICARE QUESTA SEZIONE)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.Solve(model)
    
    # Restituisce gli oggetti grezzi per permettere alla Fase 3 e 4 di manipolarli
    return status, solver, shift_vars, worker_satisfaction

if __name__ == '__main__':
    status, solver, shift_vars, worker_satisfaction = solve_shift_scheduling()                                         
""")
    print("Invocazione di Gemini 3.5 Flash")

    try:  # questo try serve per formattare pe rbene la risposta generata da gemini altrimenti può contenere altre info inutli
        parser = StrOutputParser()
        chain = prompt_template | llm | parser

        risultato_grezzo = chain.invoke({"hospital_rules": hospital_rules})

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
