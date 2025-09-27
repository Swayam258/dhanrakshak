"""
Tiny IsolationForest wrapper + heuristic keywords for fraud detection.
In real apps, you'd train on labeled scam vs ham datasets.
"""

from sklearn.ensemble import IsolationForest
import numpy as np
import re

RED_FLAGS = [
    r"urgent", r"share\s*otp", r"kyc\s*suspended", r"gift\s*card",
    r"processing\s*fee", r"verification\s*link", r"double\s*money",
    r"lottery", r"prize", r"refund\s*link", r"payment\s*link"
]
RED_FLAGS_RE = [re.compile(pat, re.IGNORECASE) for pat in RED_FLAGS]

class FraudScorer:
    def __init__(self):
        # Unsupervised toy model: numeric features = length, digits count, links count
        self.model = IsolationForest(contamination=0.1, random_state=42)
        # Fabricate some synthetic "normal" + "anomalous" samples to fit
        normal = np.random.normal(loc=[120, 1, 0], scale=[40, 1, 0.3], size=(200, 3))
        scammy = np.random.normal(loc=[260, 8, 2], scale=[60, 3, 1.0], size=(40, 3))
        X = np.vstack([normal, scammy])
        self.model.fit(X)

    def features(self, text: str):
        length = len(text)
        digits = sum(c.isdigit() for c in text)
        links = len(re.findall(r"https?://|www\.", text))
        return np.array([[length, digits, links]])

    def keyword_hits(self, text: str):
        return [r.pattern for r in RED_FLAGS_RE if r.search(text)]

    def score_text(self, text: str):
        X = self.features(text)
        pred_score = -self.model.decision_function(X)[0]  # higher = more anomalous
        hits = self.keyword_hits(text)

        # --- FIX: Increase the keyword hit weight and adjust thresholds ---
        # Blend: keyword hits are now weighted 1.0, giving a stronger signal for common scam words.
        blended = float(pred_score + 1.0 * len(hits))

        # Lowered thresholds slightly:
        # Score > 1.5 -> High (was 1.8)
        # Score > 0.5 -> Medium (was 1.0)
        if blended >= 1.5:
            risk = "high"
        elif blended >= 0.5:
            risk = "medium"
        else:
            risk = "low"

        return risk, blended, hits

fraud_scorer = FraudScorer()
