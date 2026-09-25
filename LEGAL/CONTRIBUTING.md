# CHANDRABHAR-2 Contribution & Access Policy

CHANDRABHAR-2 is proprietary software. The repository license grants no general right to copy,
modify, redistribute, or submit derivative work. Repository access is controlled by the owner.

If you have been explicitly invited as a collaborator, follow the project's technical and
scientific integrity rules below. Access as a collaborator does not transfer ownership or grant
a separate software license.

## Scientific-core rules

Changes to `app/core/*.py` that affect matching behavior, thresholds, or reported metrics must
be documented in `CHANGELOG.md`, covered by a relevant test in `tests/`, and re-validated via
`python run.py` before being described as working.

Contributors must not:
- fabricate or inflate matches, inliers, accuracy, precision, recall, RMSE, or validation status;
- bypass the evidence gate;
- introduce a GPU-only dependency that breaks CPU-first operation without an explicit design decision;
- imply ISRO endorsement, certification, or affiliation; or
- add third-party dependencies without recording their license in `LEGAL/THIRD_PARTY_NOTICES.md`.

## Process

1. Obtain explicit project-owner approval before substantial changes.
2. Run `python -m pytest -q` and `python run.py`.
3. Document scientific-behavior changes and their evidence.
4. Update affected documentation.
