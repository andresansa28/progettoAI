from worker_agent import generate_constraints
from scheduler_graph import graph
from llm_parser import parse


def main():

    #parse("preferenze.txt")

    generate_constraints(
        "preferences1.json"
    )

    initial_state = {
        "attempt": 0,
        "violations": [],
        "violation_history": [],
        "current_code": "",
        "respected": False,
        "fairness_dict": {}
    }

    config = {
        "configurable": {
            "thread_id": "hospital_scheduler"
        }
    }

    result = graph.invoke(
        initial_state,
        config=config
    )

    print("\nWorkflow terminato")


if __name__ == "__main__":
    main()