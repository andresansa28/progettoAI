from typing import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

import importlib
import sys

from drafting_agent import generate_schedule_draft
from hard_constraint_verifier import HardConstraintVerifier
from calcola_fairness import calcola_fairness_dizionario
from util import print_schedule_terminal
from config import *

LAST_SOLVER = None
LAST_SHIFTS = None


# ======================================
# STATE
# ======================================


class SchedulerState(TypedDict):
    attempt: int
    violations: list[str]
    violation_history: list[list[str]]

    current_code: str

    respected: bool

    fairness_dict: dict

    worst_worker: int
    worst_score: float
    previous_worst_score: float | None

    global_score: float
    previous_global_score: float | None

    fairness_feedback: str

    refinement_iteration: int


# ======================================
# DRAFTING NODE
# ======================================


def drafting_node(state: SchedulerState):

    # Capiamo in che fase siamo in base alla presenza del feedback di fairness
    feedback = state.get("fairness_feedback", "")
    is_refinement = bool(feedback)

    print("\n" + "=" * 70)
    if is_refinement:
        # Sottraiamo 1 perché il nodo fairness ha già incrementato l'iterazione prima di arrivare qui
        ref_iter = state.get("refinement_iteration", 1) - 1
        print(f"DRAFTING AGENT - [FASE 4] REFINEMENT FAIRNESS (Iterazione: {ref_iter})")
    else:
        att = state.get("attempt", 0)
        print(f"DRAFTING AGENT - [FASE 2] GENERAZIONE INIZIALE (Tentativo: {att})")
    print("=" * 70)

    try:
        generate_schedule_draft(
            violations=state.get("violations", []),
            previous_code=state.get("current_code", ""),
            fairness_feedback=feedback,
        )
    except Exception as e:
        raise RuntimeError(f"Errore nel Drafting Agent: {e}")

    with open("schedule_draft_model.py", "r", encoding="utf-8") as f:
        generated_code = f.read()

    return {"current_code": generated_code}


# ======================================
# SOLVER NODE
# ======================================


def solver_node(state: SchedulerState):

    global LAST_SOLVER
    global LAST_SHIFTS

    print("\n=== SOLVER ===")

    if "schedule_draft_model" in sys.modules:
        del sys.modules["schedule_draft_model"]

    import schedule_draft_model

    importlib.reload(schedule_draft_model)

    status, solver, shifts, worker_satisfaction = (
        schedule_draft_model.solve_shift_scheduling()
    )

    LAST_SOLVER = solver
    LAST_SHIFTS = shifts

    print_schedule_terminal(solver, shifts, LAVORATORI, GIORNI)

    return {}


# ======================================
# VERIFIER NODE
# ======================================


def verifier_node(state: SchedulerState):

    global LAST_SOLVER
    global LAST_SHIFTS

    print("\n=== HARD CONSTRAINT VERIFIER ===")

    verifier = HardConstraintVerifier(LAST_SOLVER, LAST_SHIFTS, LAVORATORI, GIORNI, TURNI)
    violations = verifier.verify_all_constraints()

    history = list(state.get("violation_history", []))
    history.append(violations)

    respected = len(violations) == 0
    next_attempt = state.get("attempt", 0) + 1

    if respected:
        print("Tutti i vincoli HARD sono rispettati!")
        return {
            "violations": violations,
            "violation_history": history,
            "respected": respected,
            "attempt": next_attempt,
        }
    else:
        print(f"Violazioni rilevate ({len(violations)}):")
        for v in violations:
            print(f"  - {v}")
        print(f"Rigenerazione modello necessaria.")

        return {
            "violations": violations,
            "violation_history": history,
            "respected": respected,
            "attempt": next_attempt,
            "fairness_feedback": "",
        }


# ======================================
# FAIRNESS NODE
# ======================================


def fairness_node(state: SchedulerState):
    global LAST_SOLVER
    global LAST_SHIFTS

    print("\n=== FAIRNESS EVALUATION ===")
    fairness = calcola_fairness_dizionario(LAST_SOLVER, LAST_SHIFTS, LAVORATORI, GIORNI)

    fairness_ordinato = dict(sorted(fairness.items(), key=lambda item: item[1]))
    somma_fairness = 0
    for k in fairness_ordinato:
        print(f"  Worker_{k}: {fairness_ordinato[k]}")
        somma_fairness += fairness_ordinato[k]

    print(f"Fairness globale (Somma): {somma_fairness}")

    worst_worker = min(fairness, key=fairness.get)
    worst_score = fairness[worst_worker]

    previous_score = state.get("worst_score")
    previous_global_score = state.get("global_score")

    # ==========================================
    # CALCOLO DINAMICO DELLE TOLLERANZE (BOUNDS)
    # ==========================================
    target_bounds = {}
    for w, score in fairness.items():
        if w == worst_worker:
            target_bounds[w] = score + 5
        else:
            if score >= 70:
                min_allowed = score - 15
            else:
                min_allowed = score - 10
            target_bounds[w] = max(0, min_allowed)

    feedback = f"""
    ANALISI FAIRNESS ATTUALE:
    - Lavoratore più svantaggiato: ID {worst_worker} (Punteggio: {worst_score})
    - Fairness Globale (Somma): {somma_fairness}

    DIZIONARIO DEI LIMITI MINIMI (MIN_BOUNDS):
    {target_bounds}
    """

    return {
        "fairness_dict": fairness,
        "worst_worker": worst_worker,
        "worst_score": worst_score,
        "previous_worst_score": previous_score,
        "global_score": somma_fairness,
        "previous_global_score": previous_global_score,
        "fairness_feedback": feedback,
        "refinement_iteration": state.get("refinement_iteration", 0) + 1,
    }


# ======================================
# FAIRNESS ROUTER
# ======================================

# Punteggio della fairness totale tra un'iterazione e l'altra (fairness totale è la somma dei valori di fairness di ogni lavoratore)
MAX_GLOBAL_DROP = 70


def fairness_router(state: SchedulerState):
    print("\n=== FAIRNESS UPDATE ===")

    worst_worker = state.get("worst_worker")
    
    prev_worst = state.get("previous_worst_score")
    curr_worst = state.get("worst_score")

    prev_global = state.get("previous_global_score")
    curr_global = state.get("global_score")

    iteration = state.get("refinement_iteration", 0)

    if iteration > MAX_REFINEMENTS:
        print(f"Raggiunto limite massimo di refinement ({MAX_REFINEMENTS} iterazioni).")
        return "end"

    if prev_worst is None or prev_global is None:
        print(f"Prima valutazione completata, il lavoratore peggiore è {worst_worker}. Avvio Refinement (Iterazione 0) -> DRAFT")
        return "draft"

    print("Controllo andamento metriche:")
    print(
        f"  Fairness Peggiore: peggiore precedente {prev_worst} -> peggiore attuale {curr_worst}"
    )
    print(
        f"  Fairness Globale: valore precedente {prev_global} -> valore attuale {curr_global}"
    )

    # 1. Il peggiore è PEGGIORATO
    if curr_worst < prev_worst:
        print("STOP: Il lavoratore più scontento è peggiorato. Fase 4 Conclusa -> END")
        return "end"

    # 2. Il peggiore è in STALLO (identico)
    if curr_worst == prev_worst:

        # Se il globale è costante o aumentato, continua
        if curr_global >= prev_global:
            print(
                "CONTINUA: Il peggiore è in stallo, ma la fairness globale è SALITA O COSTANTE. Esplorazione utile -> DRAFT"
            )
            return "draft"
        else:
            print(
                "STOP: Stallo del peggiore e nessun miglioramento globale. Fase 4 Conclusa -> END"
            )
            return "end"

    # 3. Il peggiore E' MIGLIORATO, ma il globale è crollato TROPPO
    if curr_global < prev_global - MAX_GLOBAL_DROP:
        print(
            f"STOP: Il peggiore è migliorato, ma la fairness globale è crollata di oltre {MAX_GLOBAL_DROP} punti. Costo collettivo troppo alto -> END"
        )
        return "end"

    # 4. Il peggiore è migliorato senza distruggere il globale
    print(
        f"La fairness del lavoratore {worst_worker} è migliorata ed anche quella globale. Continuo il Refinement -> DRAFT"
    )
    return "draft"


# ======================================
# ROUTER VINCOLI HARD
# ======================================


def hard_router(state: SchedulerState):

    is_solved = state.get("solved", False)
    current_attempt = state.get("attempt", 0)

    if is_solved:
        print(
            "\n[ROUTER VINCOLI] -> Vincoli HARD validi! Transizione alla FASE 4 (FAIRNESS) -> FAIRNESS"
        )
        return "fairness"

    if current_attempt >= MAX_ATTEMPTS:
        print(
            f"\n[ROUTER VINCOLI] -> FALLIMENTO CRITICO. Max tentativi ({MAX_ATTEMPTS}) raggiunti -> END"
        )
        return "end"

    print(
        f"\n[ROUTER VINCOLI] -> Violazioni trovate. Ritorno alla Generazione (Tentativo {current_attempt}) -> DRAFT"
    )
    return "draft"


# ======================================
# GRAPH
# ======================================

builder = StateGraph(SchedulerState)

builder.add_node("draft", drafting_node)
builder.add_node("solve", solver_node)
builder.add_node("verify", verifier_node)
builder.add_node("fairness", fairness_node)

builder.set_entry_point("draft")

builder.add_edge("draft", "solve")
builder.add_edge("solve", "verify")

builder.add_conditional_edges(
    "verify", hard_router, {"draft": "draft", "fairness": "fairness", "end": END}
)

builder.add_conditional_edges(
    "fairness", fairness_router, {"draft": "draft", "end": END}
)

memory = MemorySaver()

graph = builder.compile(checkpointer=memory)
