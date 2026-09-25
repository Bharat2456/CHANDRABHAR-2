import numpy as np
from app.core.matcher import match_representations

def test_ecc_dense_fallback_never_validates_without_independent_matches():
    rng=np.random.default_rng(4)
    a=rng.random((128,128),dtype=np.float32)
    b=a.copy()
    r=match_representations(a,b,ratio=0.5)
    # Identical textured inputs should be solved by SIFT, not the dense ECC fallback.
    assert r.diagnostics.get("matcher_path") != "ecc_affine" or r.diagnostics.get("status") != "VALIDATED"

def test_phase_dense_fallback_never_counts_as_independent_validation():
    rng=np.random.default_rng(9)
    base=rng.normal(0,1,(128,128)).astype(np.float32)
    # Blur heavily so SIFT is unavailable/weak while phase correlation can still estimate translation.
    import cv2
    a=cv2.GaussianBlur(base,(0,0),3.0)
    b=np.roll(a,3,axis=1)
    r=match_representations(a,b,ratio=0.5)
    if r.diagnostics.get('matcher_path')=='phase_correlation':
        assert r.diagnostics.get('independent_correspondence_evidence') is False
        assert r.diagnostics.get('status')=='INSUFFICIENT_EVIDENCE'
