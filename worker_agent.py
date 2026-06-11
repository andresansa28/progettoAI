from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
import os



os.environ["GOOGLE_API_KEY"] = "chiave"

def generate_constraints(file_json):

    with open(file_json, "r", encoding="utf-8") as f:
        preferences_json = f.read()

    prompt = f"""
    Sei un Senior Python Engineer specializzato in Google OR-Tools.

    Riceverai in input le preferenze dei lavoratori in formato JSON (precedentemente estratte tramite NLP).
    I DATI JSON DA USARE:
    {preferences_json}

    IL TUO OBIETTIVO:
    Genera un modulo Python indipendente che trasforma queste preferenze in una rappresentazione leggibile dalla macchina, pronta per essere importata dal Drafting Agent e passata al CP-SAT solver.

    REGOLE DI GENERAZIONE:
    Il file Python DEVE contenere le seguenti tre sezioni, in base alle specifiche di sistema:

    1. HARD CONSTRAINTS (Vincoli Personali Rigidi):
    Crea una struttura dati (es. un dizionario `UNAVAILABLE_DATES`) che mappa ogni `worker_id` alle sue date indisponibili presenti nel JSON.

    2. SOFT CONSTRAINTS (Preferenze e Tolleranze):
    Crea strutture dati per mappare i desideri. Definisci dei "pesi" costanti per la penalizzazione o la ricompensa (es. BONUS_PREFERRED_SHIFT = 5, PENALTY_DISLIKED_SHIFT = -5, BONUS_DAY_OFF = 10).
    Mappa i dati del JSON (preferred_shift, disliked_shifts, preferred_day_off) in dizionari indicizzati per `worker_id`.

    3. PREFERENCE SCORING (Modello di Soddisfazione):
    Implementa una funzione chiamata `evaluate_worker_satisfaction(worker_id, assigned_shifts, assigned_days_off)` che quantifica quanto un calendario generato soddisfa le preferenze di un lavoratore. Questa funzione servirà per calcolare le metriche di equità e soddisfazione.

    STRUTTURA OBBLIGATORIA DEL FILE:
    Restituisci ESCLUSIVAMENTE codice Python valido e pronto all'uso. Non inserire markdown, spiegazioni testuali o commenti fuori dal codice. Inizia il codice esattamente in questo modo:

    ```python
    # worker_preferences.py
    # Modulo generato automaticamente per formalizzare hard constraints e soft preferences

    # --- 1. HARD CONSTRAINTS ---
    # [Genera qui il dizionario delle indisponibilità leggendo dal JSON]
    UNAVAILABLE_DATES = {{}} 

    # --- 2. SOFT CONSTRAINTS & WEIGHTS ---
    # [Genera qui i dizionari delle preferenze e i relativi pesi leggendo dal JSON]

    # --- 3. PREFERENCE SCORING (Modello di Soddisfazione) ---
    def evaluate_worker_satisfaction(worker_id, assigned_shifts_list, assigned_days_off_list):
        \"\"\"
        Calcola il punteggio di soddisfazione per un singolo lavoratore.
        Ritorna un valore numerico (più alto = maggiore soddisfazione).
        \"\"\"
        score = 0
        # [Implementa la logica di calcolo usando i dizionari e i pesi generati sopra]
        return score

    """
    #llm = ChatOllama(model="glm-4.7:cloud", temperature=0)
    # llm = ChatOpenAI(
    #     model="poolside/laguna-m.1:free",
    #     base_url="https://openrouter.ai/api/v1", 
    #     api_key="chiave",
    #     temperature=0,  
    # )
    llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
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
