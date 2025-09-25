import joblib, numpy as np, pandas as pd
m = joblib.load("models/final_model.joblib")
s = joblib.load("models/test_split.joblib")
p = m.predict_proba(s["test_x"])[:,1]
print("min/median/max:", p.min(), np.median(p), p.max(), " FAIL ratio:", (p>=0.5).mean())