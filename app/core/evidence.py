def gate(result):
 d=result.diagnostics or {}; reasons=[]
 if result.tentative_matches<8: reasons.append('too_few_tentative_matches')
 if result.inliers<12: reasons.append('too_few_inliers')
 if result.inlier_ratio<0.35: reasons.append('low_inlier_ratio')
 if result.coverage<0.35: reasons.append('low_spatial_coverage')
 if result.rmse_px is None or result.rmse_px>2.5: reasons.append('high_or_missing_rmse')
 return {'status':'VALIDATED' if not reasons else 'INSUFFICIENT_EVIDENCE','reasons':reasons}
