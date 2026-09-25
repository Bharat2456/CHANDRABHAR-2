# LunaMatch Platform — Final Prototype

## What this is

A presentation-ready frontend around the audited LunaMatch v8.0.2 scientific engine. The engine is frozen; this package adds the visible platform layer.

The platform provides:
- Chandrayaan-2 mission-data inventory
- OHRC / TMC-2 / IIRS product cards
- browse-image previews
- physical GSD and Sun-angle context
- interactive reference/source selection
- visible pipeline stages
- live correspondence execution status
- match/inlier/coverage/RMSE metrics
- scale-cascade diagnostics
- correspondence-density visualization
- evidence-gate explanation
- JSON result export

## Data

Keep your real mission data outside this package, for example:
`<YOUR_MISSION_DATA_ROOT>`

The application reads the data locally and does not upload it.

## Start

Double-click `RUN_PLATFORM.bat`, or run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run dashboard.py
```

Then open the local address Streamlit prints, normally `http://localhost:8501`.

## Scientific positioning

The frontend does not manufacture validation. The evidence gate remains conservative. Real mission-data results must be interpreted separately from synthetic benchmark results, and the current three-sensor experiment should not be described as fully validated unless the evidence gate actually supports that claim.

## Engine baseline

Scientific core: LunaMatch v8.0.2.
Platform layer: Final Prototype Platform 1.0.
