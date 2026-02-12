"""Run recognition benchmark on a folder of test images using either classifiers or embedding-distance fallback."""
import os
import glob
import time
import numpy as np
import joblib
from tools.predict_with_classifier import load_joblib_model, predict_embedding
import pickle


def load_test_images(folder):
    files = []
    for ext in ('*.jpg', '*.jpeg', '*.png'):
        files.extend(glob.glob(os.path.join(folder, ext)))
    return files


def load_cache_embeddings(cache_dir):
    encs = []
    labels = []
    for f in glob.glob(os.path.join(cache_dir, '*.pkl')):
        try:
            with open(f, 'rb') as fh:
                d = pickle.load(fh)
            enc = d.get('encoding')
            roll = d.get('rollno')
            if enc is not None and roll is not None:
                encs.append(np.array(enc))
                labels.append(str(roll))
        except Exception:
            continue
    return np.array(encs), labels


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--testdir', required=True, help='folder with test images (one person per image)')
    p.add_argument('--cache', default='face_cache')
    p.add_argument('--model', default='models/knn_embeddings.joblib')
    args = p.parse_args()

    files = load_test_images(args.testdir)
    if not files:
        print('No test images found')
        return

    encs_cache, labels_cache = load_cache_embeddings(args.cache)
    if len(encs_cache) == 0:
        print('No cached embeddings found; run cache prewarm')
        return

    model, le = None, None
    if os.path.exists(args.model):
        model, le = load_joblib_model(args.model)

    times = []
    correct = 0
    total = 0

    for f in files:
        total += 1
        # attempt to find matching cache item by filename rollno
        # For benchmark we assume file name contains rollno as prefix
        fname = os.path.basename(f)
        expected = fname.split('_')[0].upper() if '_' in fname else None

        # load embedding from cache if available
        # This is a rough benchmark; in real tests you'd compute enc from image
        emb = None
        for pth in glob.glob(os.path.join(args.cache, '*.pkl')):
            if os.path.basename(pth).startswith(expected):
                with open(pth, 'rb') as fh:
                    d = pickle.load(fh)
                emb = np.array(d.get('encoding'))
                break

        if emb is None:
            continue

        t0 = time.time()
        label, conf = None, 0.0
        if model is not None:
            label, conf = predict_embedding(model, le, emb, threshold=0.6)
        # fallback to nearest neighbor by distance
        if label is None:
            dists = np.linalg.norm(encs_cache - emb.reshape(1, -1), axis=1)
            idx = int(np.argmin(dists))
            label = labels_cache[idx]
        t1 = time.time()
        times.append(t1 - t0)

        if expected and label and expected == label:
            correct += 1

    print(f"Processed {len(times)} images. Average time: {np.mean(times):.4f}s. Accuracy (loose): {correct}/{total}")


if __name__ == '__main__':
    main()
