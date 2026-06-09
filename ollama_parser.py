from typing import List, Optional

from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# =====================================================
# SCHEMA JSON
# =====================================================


class WorkerPreference(BaseModel):

    worker_id: int = Field(description="Identificativo del lavoratore")

    preferred_shift: Optional[str] = Field(
        default=None, description="Turno preferito: MATTINA, POMERIGGIO o NOTTE"
    )

    preferred_day_off: Optional[str] = Field(
        default=None, description="Giorno libero preferito"
    )

    disliked_shifts: List[str] = Field(
        default_factory=list, description="Turni sgraditi"
    )

    unavailable_dates: List[str] = Field(
        default_factory=list, description="Giorni in cui il lavoratore non può lavorare"
    )


class PreferencesFile(BaseModel):

    workers: List[WorkerPreference]


# =====================================================
# PROMPT
# =====================================================

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
Sei un sistema di estrazione informazioni.

Riceverai un file contenente le preferenze di più lavoratori.

Per ogni lavoratore estrai:

- worker_id
- preferred_shift
- preferred_day_off
- disliked_shifts
- unavailable_dates

Regole:

preferred_shift:
MORNING
AFTERNOON
NIGHT

preferred_day_off:
MONDAY
TUESDAY
THURSDAY
FRIDAY
SATURDAY
SUNDAY

HOLIDAY DATE MAPPING

Considera le seguenti espressioni equivalenti per le festività, e mappa ciascuna di esse alla data corrispondente:

Christmas Eve:
- Christmas Eve
- Christmas eve
- December 24
- 24 December
- 24th December
-> 2025-12-24

Christmas:
- Christmas
- Christmas Day
- December 25
- 25 December
- 25th December
-> 2025-12-25

St. Stephen's Day:
- St. Stephen's Day
- Saint Stephen's Day
- Santo Stefano
- December 26
- 26 December
- 26th December
-> 2025-12-26

New Year's Eve:
- New Year's Eve
- New Years Eve
- December 31
- 31 December
- 31st December
-> 2025-12-31

New Year's Day:
- New Year's Day
- New Year
- January 1
- 1 January
- 1st January
-> 2026-01-01

Se un lavoratore dichiara di non voler lavorare in una festività,
inserisci la data corrispondente in unavailable_dates.

Restituisci esclusivamente dati conformi allo schema.

Se un'informazione non è presente usa null oppure [].
""",
        ),
        ("user", "{text}"),
    ]
)

# =====================================================
# OLLAMA
# =====================================================

llm = ChatOllama(model="llama3.1:8b", temperature=0).with_structured_output(
    PreferencesFile
)


# =====================================================
# FUNZIONE ESTRAZIONE
# =====================================================


def extract_preferences(text: str):

    chain = prompt | llm

    result = chain.invoke({"text": text})

    return result


def parse(path_file):

    with open(path_file, "r") as f:
        text = f.read()

    print("Lettura file testule in corso")
    preferences = extract_preferences(text)
    # print(preferences.model_dump_json(indent=4))
    # Creazione fisica del file
    with open("preferences1.json", "w", encoding="utf-8") as f:
        f.write(preferences.model_dump_json(indent=4))
        print("Json creato correttamente")
    