"""
Voynich OS — Cluster Meaning Engine v3.3 (entry module)

Thin wrapper around cluster_theme_builder_v3_3.run_v3_3_pipeline().
Keeps execution simple and inspectable: python -m engine.cluster_meaning_v3_3
"""

from __future__ import annotations

from .cluster_theme_builder_v3_3 import run_v3_3_pipeline


def main() -> None:
    run_v3_3_pipeline()


if __name__ == "__main__":
    main()
