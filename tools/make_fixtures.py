"""CLI wrapper: python tools/make_fixtures.py [outdir]  (generator lives in app/synthetic.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.synthetic import build_archive, build_misc
if __name__ == '__main__':
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'tests/fixtures/synthetic_archive')
    print(build_archive(out)); build_misc(out/'misc'); print('written to', out)
