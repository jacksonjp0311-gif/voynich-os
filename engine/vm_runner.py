\"\"\"Command-line runner for Voynich OS (public-safe).

Allows simple experiments from the terminal:
    python -m engine.vm_runner --line \"qokedy qokain\"
\"\"\"

import argparse
from .tokenizer import tokenize
from .vm import run_vm
from .transition_graph import vm_output_to_nx

def main() -> None:
    parser = argparse.ArgumentParser(
        description=\"Run a simple Voynich OS line through the VM.\"
    )
    parser.add_argument(
        \"--line\",
        type=str,
        required=True,
        help=\"EVA transcription line to process\",
    )
    args = parser.parse_args()

    tokens = tokenize(args.line)
    vm_graph = run_vm(tokens)
    g = vm_output_to_nx(vm_graph)

    print(\"Tokens:\", tokens)
    print(\"Nodes:\")
    for n, data in g.nodes(data=True):
        print(f\"  {n}: {data}\")
    print(\"Edges:\")
    for u, v in g.edges():
        print(f\"  {u} -> {v}\")

if __name__ == \"__main__\":
    main()
