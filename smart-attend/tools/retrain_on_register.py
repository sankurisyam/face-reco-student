"""Wrapper to retrain classifiers after a new registration.
This script simply invokes the embeddings training script. It is intended
to be called non-blocking from `register.py` after a successful new enrollment.
"""
import subprocess
import sys
import os


def retrain(cache_dir='face_cache', outdir='models'):
    cmd = [sys.executable, os.path.join('tools', 'train_embeddings_classifier.py'), '--cache', cache_dir, '--outdir', outdir]
    try:
        subprocess.Popen(cmd)
        return True
    except Exception as e:
        print(f"Failed to start retrain process: {e}")
        return False


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--cache', default='face_cache')
    p.add_argument('--outdir', default='models')
    args = p.parse_args()
    ok = retrain(args.cache, args.outdir)
    print('retrain started' if ok else 'retrain failed')
