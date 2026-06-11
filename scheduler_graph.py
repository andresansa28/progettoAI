from typing import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

import importlib
import sys

from drafting_agent import generate_schedule_draft
from hard_constraint_verifier import HardConstraintVerifier
from calcola_fairness import calcola_fairness_dizionario
from util import print_schedule_terminal

MAX_ATTEMPTS = 5

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

    solved: bool

    fairness_dict: dict


# ======================================
# DRAFTING NODE
# ======================================

def drafting_node(state: SchedulerState):

    print("\n" + "=" * 60)
    print(f"DRAFTING AGENT - TENTATIVO {state['attempt']}")
    print("=" * 60)

    try:

        generate_schedule_draft(
            violations=state["violations"],
            previous_code=state["current_code"]
        )

    except Exception as e:

        raise RuntimeError(
            f"Errore nel Drafting Agent: {e}"
        )

    with open(
        "schedule_draft_model.py",
        "r",
        encoding="utf-8"
    ) as f:

        generated_code = f.read()

    return {
        "current_code": generated_code
    }


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

    print_schedule_terminal(
        solver,
        shifts,
        13,
        31
    )

    return {}


# ======================================
# VERIFIER NODE
# ======================================

def verifier_node(state: SchedulerState):

    global LAST_SOLVER
    global LAST_SHIFTS

    print("\n=== HARD CONSTRAINT VERIFIER ===")

    verifier = HardConstraintVerifier(
        LAST_SOLVER,
        LAST_SHIFTS,
        13,
        31,
        3
    )

    violations = verifier.verify_all_constraints()

    history = list(state["violation_history"])
    history.append(violations)

    solved = len(violations) == 0

    if solved:

        print("\nTutti i vincoli HARD sono rispettati!")

    else:

        print(f"\nViolazioni rilevate ({len(violations)}):")

        for v in violations:
            print(f"- {v}")

        print(
            f"\nRigenerazione modello - tentativo {state['attempt'] + 1}"
        )

    return {
        "violations": violations,
        "violation_history": history,
        "solved": solved,
        "attempt": state["attempt"] + 1
    }


# ======================================
# FAIRNESS NODE
# ======================================

def fairness_node(state: SchedulerState):

    global LAST_SOLVER
    global LAST_SHIFTS

    print("\n=== FAIRNESS ===")

    fairness = calcola_fairness_dizionario(
        LAST_SOLVER,
        LAST_SHIFTS,
        13,
        31
    )

    print("\nDizionario Fairness:")

    for worker, score in fairness.items():

        print(
            f"Worker {worker}: {score}"
        )

    if fairness:

        lavoratore_peggiore = min(
            fairness,
            key=fairness.get
        )

        print(
            f"\nLavoratore più svantaggiato: "
            f"{lavoratore_peggiore}"
        )

        print(
            f"Punteggio: "
            f"{fairness[lavoratore_peggiore]}"
        )

    return {
        "fairness_dict": fairness
    }


# ======================================
# ROUTER
# ======================================

def router(state: SchedulerState):

    if state["solved"]:

        print("\nRouting -> FAIRNESS")

        return "fairness"

    if state["attempt"] >= MAX_ATTEMPTS:

        print(
            f"\nNumero massimo di tentativi "
            f"({MAX_ATTEMPTS}) raggiunto."
        )

        return "end"

    print(
        f"\nRouting -> DRAFT "
        f"(tentativo {state['attempt']})"
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
    "verify",
    router,
    {
        "draft": "draft",
        "fairness": "fairness",
        "end": END
    }
)

builder.add_edge("fairness", END)

memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory
)