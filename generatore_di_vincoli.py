from langchain_openai import ChatOpenAI


with open("SmartScheduler.py", "r", encoding="utf-8") as f:
    scheduler_code = f.read()

with open("config.py", "r", encoding="utf-8") as f:
    config_code = f.read()

with open("preferences.json", "r", encoding="utf-8") as f:
    preferences_json = f.read()

prompt = f"""
Sei un Senior Python Engineer specializzato in Google OR-Tools.

Qui c'è il codice del mio scheduler principale (SOLO PER CONTESTO, per farti capire le variabili in gioco):
{scheduler_code}

Qui c'è il file di configurazione (SOLO PER CONTESTO):
{config_code}

Qui ci sono le preferenze dei lavoratori in JSON (I DATI DA USARE):
{preferences_json}

IL TUO OBIETTIVO:
Genera un file Python indipendente che contiene i vincoli aggiuntivi basati sul JSON. 
Non devi riscrivere il mio scheduler, non ridefinire il solver, non ridefinire i turni. Devi generare SOLO la funzione delle preferenze.

STRUTTURA OBBLIGATORIA DEL FILE (Inizia esattamente così e non cambiare i parametri della funzione):
```python
from datetime import date, timedelta, datetime

def add_preferences(model, shifts, lavoratori, giorni_totali, turni_totali, DAYS_LIST):
    objective_terms = []
    
    # [INSERISCI QUI LA LOGICA PER OGNI LAVORATORE LEGGENDO DAL JSON]
    # Usa DAYS_LIST per mappare le date.
    
    return objective_terms"""


def generate_constraints():

    llm = ChatOpenAI(
        model="nvidia/nemotron-3-ultra-550b-a55b:free",
        base_url="https://openrouter.ai/api/v1", 
        api_key="inserire-chiave-openrouter",
        temperature=0,  
    )

    print("Generazione dei vincoli in corso")

    try:
        result = llm.invoke(prompt)

        # --- INIZIO FIX PER GEMINI ---
        contenuto = result.content

        if isinstance(contenuto, list):
            # Estraiamo il testo dal primo blocco della lista
            testo_grezzo = contenuto[0].get("text", "")
        else:
            # Se è già una normale stringa, la teniamo così
            testo_grezzo = contenuto
        # --- FINE FIX ---

        # Ora facciamo la pulizia in totale sicurezza sulla stringa estratta
        codice = (
            testo_grezzo.replace("```python\n", "")
            .replace("```python", "")
            .replace("```", "")
            .strip()
        )

        # Creazione fisica del file
        with open("LLM_constraints.py", "w", encoding="utf-8") as f:
            f.write(codice)

        print(
            "SUCCESSO ASSOLUTO! Vincoli perfetti generati nel file 'LLM_constraints.py'!"
        )

    except Exception as e:
        print(f"ERRORE durante la generazione: {e}")


if __name__ == "__main__":
    generate_constraints()
