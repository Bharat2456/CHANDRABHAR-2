# Evidence-gate thresholds: single source of truth (the UI reads these, never re-declares them).
GATE_THRESHOLDS={'min_tentative_matches':8,'min_inliers':12,'min_inlier_ratio':0.35,'min_coverage':0.35,'max_rmse_px':2.5,'ransac_reproj_px':3.0}
def gate(result):
 d=result.diagnostics or {}; reasons=[]; T=GATE_THRESHOLDS
 if result.tentative_matches<T['min_tentative_matches']: reasons.append('too_few_tentative_matches')
 if result.inliers<T['min_inliers']: reasons.append('too_few_inliers')
 if result.inlier_ratio<T['min_inlier_ratio']: reasons.append('low_inlier_ratio')
 if result.coverage<T['min_coverage']: reasons.append('low_spatial_coverage')
 if result.rmse_px is None or result.rmse_px>T['max_rmse_px']: reasons.append('high_or_missing_rmse')
 return {'status':'VALIDATED' if not reasons else 'INSUFFICIENT_EVIDENCE','reasons':reasons}
