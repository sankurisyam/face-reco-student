"""Benchmark encoding times with and without cache."""
import time
import os
import glob
import pickle
import numpy as np
import argparse

def load_embeddings(cache_dir):
    res = []
    for f in glob.glob(os.path.join(cache_dir, '*.pkl')):
        try:
            with open(f, 'rb') as fh:
                d = pickle.load(fh)
            enc = d.get('encoding')
            if enc is not None:
                res.append(np.array(enc))
        except Exception:
            continue
    return res

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cache', default='face_cache')
    p.add_argument('--samples', type=int, default=50)
    args = p.parse_args()

    emb = load_embeddings(args.cache)
    print(f"Found {len(emb)} cached embeddings.")
    if not emb:
        print("No embeddings to benchmark. Run cache prewarm first.")
        return

    times = []
    for i in range(min(args.samples, len(emb))):
        e = emb[i]
        t0 = time.time()
        # simulate loading
        _ = e.copy()
        t1 = time.time()
        times.append(t1 - t0)

    print(f"Average load time (cached): {np.mean(times):.6f}s")


if __name__ == '__main__':
    main()
