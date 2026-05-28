# Voynich OS â€” Reproducibility Notes

## Purpose

This document defines the minimum reproducibility boundary for Voynich OS outputs.

A generated output should be treated as evidence only when its source corpus, engine version, command path, and output location are clear.

## Required artifact metadata

Every generated layer should ideally preserve:

- input corpus path;
- input corpus hash when possible;
- engine script or module used;
- engine version or repo commit;
- command used;
- timestamp;
- output folder;
- output count;
- summary metrics;
- known limitations;
- claim boundary.

## Current output families

Known output families include:

- data/corpus/
- data/folio_outputs/
- data/meaning/meaning_v3_1/
- data/meaning/meaning_v3_2/
- data/hybrid_v1_0/
- data/manuscript_v12_0/
- data/fields_v11/
- data/ledger/
- logs/
- state/

## Reproducibility standard

An output is considered reproducible when a clean checkout can regenerate it from documented commands without manual hidden state.

## Evidence limitation

Existing checked-in outputs are useful as artifacts, but they should not be treated as validated evidence unless their regeneration path is documented and repeatable.

## Recommended next step

Add a single command or script that regenerates the core pipeline.

Current audit command:

    python scripts/voynich_repo_audit.py