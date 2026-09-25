# SIH Project Summary — CHANDRABHAR-2

## Problem

Chandrayaan-2's three imagers (OHRC ~0.3 m, TMC-2 ~5 m, IIRS ~80 m hyperspectral) image the same
lunar terrain at wildly different scales, modalities, sun angles, and acquisition dates.
Establishing reliable geometric correspondence between them is a prerequisite for combining their
information, but is not solvable by naive feature matching. See
[`../docs/02_PROBLEM_STATEMENT.md`](../docs/02_PROBLEM_STATEMENT.md).

## Solution approach

CHANDRABHAR-2 implements a full, inspectable pipeline: format-aware product discovery → true
geographic footprint intersection → a common physical-GSD grid both sensors are warped onto →
illumination-aware representation → a multi-method matcher cascade with RANSAC verification → a
fixed, documented evidence gate that only reports success when specific, quantified thresholds
are met. See [`../docs/03_SYSTEM_ARCHITECTURE.md`](../docs/03_SYSTEM_ARCHITECTURE.md).

## What is implemented and tested today

- The complete pipeline described above, CPU-only, no GPU dependency.
- 18/18 unit and integration tests passing.
- A synthetic, known-answer self-test that exercises the full chain end to end and is correctly
  gated `VALIDATED`.
- A four-tab dashboard (Mission Overview / Correspondence Lab / Evidence & Metrics / Products &
  Export) with live per-stage workflow status and export packaging.

## What is explicitly not yet claimed

Real-data scientific validation across all three Chandrayaan-2 sensor pairs has not been
asserted in this delivery — see
[`../docs/10_VALIDATION_AND_EVIDENCE.md`](../docs/10_VALIDATION_AND_EVIDENCE.md) and
[`../docs/CLAIMS_MATRIX.md`](../docs/CLAIMS_MATRIX.md). This is by design: the project's evidence
gate is built specifically so this claim can never be made prematurely.

## Team / provenance

See [`../CHANGELOG.md`](../CHANGELOG.md) for the project's development history from its original
"LunaMatch" codebase through to CHANDRABHAR-2.
