# voynich-os

Voynich OS is a computational reconstruction of the Voynich Manuscript as a symbolic process language.  
It provides a tokenizer, relational-operator classifier, state-suffix model, formal grammar, and a safe,
reproducible virtual-machine layer capable of interpreting manuscript text into structured state-transition
graphs.

This repository is intentionally simple, deterministic, and non-adaptive. It is designed for open research
and reproducible analysis of the manuscript’s glyph structure.

voynich-os
│
├── README.md – Project overview and usage
├── LICENSE – MIT license
├── .gitignore
├── requirements.txt – Python dependencies
│
├── engine/ – Public-safe Voynich OS v1.1 engine
│ ├── tokenizer.py – Token segmentation
│ ├── parser.py – Structural parser
│ ├── rel_classifier.py – REL prefix classifier
│ ├── state_classifier.py – STATE suffix classifier
│ ├── vm.py – Minimal deterministic virtual machine
│ ├── bnf_grammar.py – Static formal grammar
│ ├── transition_graph.py – Graph builder
│ └── vm_runner.py – Command-line runner
│
├── examples/ – Demonstration EVA lines
│ ├── F1r.json
│ ├── F39v.json
│ └── F70r.json
│
└── docs/
├── figures/ – Supporting diagrams (placeholder)
└── paper/
└── voynich_os_preprint_v1_0.tex – Research preprint

Author: James Paul Jackson  
License: MIT  
