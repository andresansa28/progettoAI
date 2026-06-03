import json
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

def estrai_preferenze_langchain(file_txt, nome_modello="llama3.1:8b"):
    try:
        with open(file_txt, "r", encoding="utf-8") as f:
            testo = f.read()
    except FileNotFoundError:
        return f"Errore: Il file {file_txt} non è stato trovato."

    llm = ChatOllama(
        model=nome_modello,
        temperature=0,
        num_predict=3000,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Analizza le preferenze dei lavoratori e trasformale in dati strutturati.
        Restituisci SOLO un JSON valido, senza Markdown.
        
        Usa ESCLUSIVAMENTE questo formato (una lista di oggetti), PER OGNI LAVORATORE, QUINDI IN TOTALE 10 :
        [
          {{
            "worker": "<nome_lavoratore>",
            "preferred_shift": "MORNING" | "AFTERNOON" | "NIGHT" | null,
            "uncomfortable_shifts": [
              {{
                "type": "NIGHT_SHIFT" | "HOLIDAY_SHIFT" | "SPECIFIC_DATE" | "CONSECUTIVE_SHIFT_SEQUENCE" | "CONSECUTIVE_WORKDAYS" | "WEEKEND_SHIFT",
                "shift": "MORNING" | "AFTERNOON" | "NIGHT" | null,
                "date": "YYYY-MM-DD" | null,
                "max": <numero_massimo> | null
              }}
            ],
            "availability": {{
              "available_every_day": true | false | null,
              "available_days": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"] | null,
              "unavailable_days": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"] | null,
              "available_dates": ["YYYY-MM-DD"] | null,
              "unavailable_dates": ["YYYY-MM-DD"] | null,
              "available_holidays": true | false | null,
              "available_weekends": true | false | null
            }}
          }}
        ]

        Regole di estrazione:
        - "preferred_shift" indica il turno preferito principale.
        - Le date del periodo sono dal 2026-12-07 al 2027-01-06.
        - Natale = 2026-12-25, Santo Stefano = 2026-12-26, Capodanno = 2027-01-01, Vigilia di Natale = 2026-12-24, Vigilia di capodanno = 2026-12-31
        - Se un'informazione manca, usa null o []."""),
        
        # Questa variabile {testo} verrà riempita automaticamente da LangChain
        ("user", "Ecco il testo da analizzare:\n{testo}")
    ])

    chain = prompt | llm

    print("Sto facendo ragionare l'agente sulle preferenze...")
    risposta = chain.invoke({"testo": testo})


    try:
        # Convertiamo la stringa JSON in una vera Lista di Dizionari Python
        dati_strutturati = json.loads(risposta.content)
        return dati_strutturati
    except json.JSONDecodeError:
        return "Errore: Il modello non ha generato un JSON valido."

if __name__ == "__main__":
    
    risultato = estrai_preferenze_langchain("prova2.txt", nome_modello="llama3.1:8b")
    
    # Stampiamo il risultato ben formattato
    print("\nEstrazione completata!")
    print(json.dumps(risultato, indent=2))