"""Train KNN and SVM classifiers using cached embeddings in face_cache/.
Saves models to the `models/` directory as joblib files.
"""
import os
import glob
import pickle
import joblib
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import argparse


def load_cache_embeddings(cache_dir):
    X, y = [], []
    for f in glob.glob(os.path.join(cache_dir, '*.pkl')):
        try:
            with open(f, 'rb') as fh:
                d = pickle.load(fh)
            # Avoid using truthiness on numpy arrays (raises ValueError)
            enc = d.get('encoding') if d.get('encoding') is not None else d.get('emb')
            # Pick a roll/label field reliably without boolean checks
            if d.get('rollno') is not None:
                roll = d.get('rollno')
            elif d.get('label') is not None:
                roll = d.get('label')
            else:
                roll = d.get('name')

            if enc is None or roll is None:
                continue

            enc_arr = np.array(enc)
            if enc_arr.size == 0:
                # empty encoding, skip
                continue

            X.append(enc_arr.reshape(-1))
            y.append(str(roll))
        except Exception as e:
            print(f"Skipping {f}: {e}")
    return np.array(X), np.array(y)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cache', default='face_cache', help='face_cache dir')
    p.add_argument('--outdir', default='models', help='output dir')
    p.add_argument('--test-size', type=float, default=0.2)
    p.add_argument('--knn-k', type=int, default=3)
    args = p.parse_args()

    X, y = load_cache_embeddings(args.cache)
    if len(X) == 0:
        print("No embeddings found in", args.cache)
        return

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # Check class distribution to decide whether stratified split is possible
    unique, counts = np.unique(y_enc, return_counts=True)
    class_counts = dict(zip(le.inverse_transform(unique), counts))

    if len(unique) < 2:
        print("Only one class present in data; need at least 2 different labels to train classifiers.")
        return

    min_count = counts.min()

    # If any class has fewer than 2 samples we cannot do a meaningful stratified split
    if min_count < 2:
        print(f"Warning: some classes have fewer than 2 samples: {class_counts}.")
        print("Training KNN on the full dataset (no test split) and skipping SVM evaluation.")
        # Train a KNN model on the full dataset so it can be used as a nearest-neighbor lookup at runtime.
        effective_k = min(args.knn_k, max(1, len(X)))
        if effective_k != args.knn_k:
            print(f"Adjusting K for KNN from {args.knn_k} to {effective_k} due to small dataset size.")
        knn = KNeighborsClassifier(n_neighbors=effective_k, metric='euclidean', n_jobs=-1)
        knn.fit(X, y_enc)
        os.makedirs(args.outdir, exist_ok=True)
        joblib.dump({'model': knn, 'label_encoder': le}, os.path.join(args.outdir, 'knn_embeddings.joblib'))
        print("Saved KNN model to", args.outdir)
        print("Skipping SVM training due to insufficient samples per class.")
        return

    stratify = y_enc
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=args.test_size, stratify=stratify, random_state=42
    )

    os.makedirs(args.outdir, exist_ok=True)

    # Train KNN
    # Ensure k is not larger than available training samples
    effective_k = min(args.knn_k, max(1, len(X_train)))
    if effective_k != args.knn_k:
        print(f"Adjusting K for KNN from {args.knn_k} to {effective_k} due to small training set size.")
    knn = KNeighborsClassifier(n_neighbors=effective_k, metric='euclidean', n_jobs=-1)
    knn.fit(X_train, y_train)
    if len(X_test) > 0:
        y_pred = knn.predict(X_test)
        print("KNN accuracy:", accuracy_score(y_test, y_pred))
        unique_test = np.unique(y_test)
        if len(unique_test) >= 2:
            try:
                target_names = list(le.inverse_transform(unique_test))
                print(classification_report(y_test, y_pred, labels=unique_test, target_names=target_names))
            except Exception as e:
                print("KNN report skipped due to:", e)
        else:
            print("KNN: test split contains fewer than 2 classes; skipping detailed report.")
    else:
        print("KNN: no test data available to evaluate.")
    joblib.dump({'model': knn, 'label_encoder': le}, os.path.join(args.outdir, 'knn_embeddings.joblib'))

    # Train SVM
    svm = SVC(kernel='rbf', probability=True)
    svm.fit(X_train, y_train)
    if len(X_test) > 0:
        try:
            y_pred = svm.predict(X_test)
            print("SVM accuracy:", accuracy_score(y_test, y_pred))
            unique_test = np.unique(y_test)
            if len(unique_test) >= 2:
                try:
                    target_names = list(le.inverse_transform(unique_test))
                    print(classification_report(y_test, y_pred, labels=unique_test, target_names=target_names))
                except Exception as e:
                    print("SVM report skipped due to:", e)
            else:
                print("SVM: test split contains fewer than 2 classes; skipping detailed report.")
        except Exception as e:
            print("SVM evaluation failed:", e)
    else:
        print("SVM: no test data available to evaluate.")
    joblib.dump({'model': svm, 'label_encoder': le}, os.path.join(args.outdir, 'svm_embeddings.joblib'))

    print("Saved models to", args.outdir)


if __name__ == '__main__':
    main()
