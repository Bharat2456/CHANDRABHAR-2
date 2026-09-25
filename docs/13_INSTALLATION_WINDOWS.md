# 13 — Installation (Windows)

CHANDRABHAR-2 targets Windows first (the environment used during development), and also runs on
Linux/macOS with the same commands minus the PowerShell-specific syntax.

## Prerequisites

- **Python 3.10 or newer** (64-bit). Check with `python --version`.
- No GPU required.
- No internet access required at runtime (only during `pip install`).

## Step-by-step

1. **Clone or unzip the project**, then open PowerShell in the project root.

2. **Create and activate a virtual environment:**
   ```powershell
   py -3.10 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. **(Optional) install extras** — `requirements.txt` already pulls in Shapely and SciPy (used
   for exact polygon intersection and geometry interpolation); `requirements-optional.txt` adds
   further geospatial format support (shapefiles, rasterio, pyproj) not required for the core
   pipeline:
   ```powershell
   python -m pip install -r requirements-optional.txt
   ```

5. **Verify the install:**
   ```powershell
   python -m pytest -q
   python run.py
   ```
   Expected: `18 passed` and `CHANDRABHAR-2 ENGINE SELF-TEST PASSED`.

6. **Launch the dashboard:**
   ```powershell
   RUN_CHANDRABHAR-2.bat
   ```
   or
   ```powershell
   python -m streamlit run dashboard.py
   ```
   Streamlit opens `http://localhost:8501` in your default browser.

## Dependencies actually used

See [`LEGAL/THIRD_PARTY_NOTICES.md`](../LEGAL/THIRD_PARTY_NOTICES.md) for the full list with
license and purpose. Directly required (`requirements.txt`): NumPy, OpenCV (`opencv-python`),
Shapely, SciPy, Streamlit. Streamlit itself pulls in Pillow, pandas and pyarrow as transitive
dependencies (used by its UI widgets, not called directly by CHANDRABHAR-2's own code). Optional
(`requirements-optional.txt`): pyshp, rasterio, pyproj. Dev-only (`requirements-dev.txt`):
pytest.

## Troubleshooting the install

See [`docs/16_TROUBLESHOOTING.md`](16_TROUBLESHOOTING.md).
