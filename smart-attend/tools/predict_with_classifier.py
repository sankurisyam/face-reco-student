"""Simple wrapper to load a saved classifier and predict a label + confidence for an embedding.
"""
import joblib
import numpy as np
import os


def load_joblib_model(path):
    if not os.path.exists(path):
        return None, None
    d = joblib.load(path)
    return d.get('model'), d.get('label_encoder')


def predict_embedding(model, le, embedding, threshold=0.6):
    """Return (label, confidence) or (None, conf) if below threshold."""
    if model is None or le is None:
        return None, 0.0

    emb = np.array(embedding).reshape(1, -1)
    # Prefer probability outputs
    try:
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(emb)[0]
            idx = int(np.argmax(probs))
            conf = float(probs[idx])
            label = le.inverse_transform([idx])[0]
            if conf < threshold:
                return None, conf
            return label, conf
    except Exception:
        pass

    # Try KNN distance-based heuristic
    try:
        if hasattr(model, 'kneighbors'):
            dists, idxs = model.kneighbors(emb, n_neighbors=min(getattr(model, 'n_neighbors', 3), len(model._fit_X)))
            # Use mean distance as heuristic (lower -> better)
            avg_dist = float(dists.mean())
            # map to [0,1]
            conf = max(0.0, 1.0 - (avg_dist / 0.6))
            pred = model.predict(emb)[0]
            label = le.inverse_transform([pred])[0]
            if conf < threshold:
                return None, conf
            return label, conf
    except Exception:
        pass

    # Fallback: direct predict without confidence
    try:
        pred = model.predict(emb)[0]
        label = le.inverse_transform([pred])[0]
        return label, 0.5
    except Exception:
        return None, 0.0


if __name__ == '__main__':
    # quick CLI for testing
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--emb', required=True, help='path to npy file containing embedding')
    p.add_argument('--threshold', type=float, default=0.6)
    args = p.parse_args()
    model, le = load_joblib_model(args.model)
    emb = np.load(args.emb)
    lbl, conf = predict_embedding(model, le, emb, threshold=args.threshold)
    print(lbl, conf)
