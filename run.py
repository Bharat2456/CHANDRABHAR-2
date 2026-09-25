from app.selftest import run
r=run(); print('CHANDRABHAR-2 ENGINE SELF-TEST', 'PASSED' if r['passed'] else 'FAILED'); print(r); raise SystemExit(0 if r['passed'] else 1)
