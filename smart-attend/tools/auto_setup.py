"""Auto prewarm face cache and train classifiers in background.
This script is intended to be launched as a separate process by `main.py`.
It tries to prewarm the `face_cache/` by scanning `Images_Attendance/` and
calling `batch_encode_and_cache`, then runs the trainer to produce models.
If dependencies (dlib/face_recognition) are missing the script exits gracefully.
"""
import os
import sys
import subprocess
import time
import traceback

# Ensure project root is on sys.path so imports like `face_encoding_cache` work
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def prewarm_cache():
    try:
        from face_encoding_cache import FaceEncodingCache, batch_encode_and_cache
    except Exception as e:
        print("Auto-setup: face_encoding_cache import failed:", e)
        return False

    images_path = 'Images_Attendance'
    if not os.path.exists(images_path):
        print('Auto-setup: Images_Attendance not found, skipping prewarm.')
        return False

    students_data = []
    valid_prefixes = ('22FE1A', '23FE5A')
    for root, dirs, files in os.walk(images_path):
        for cl in files:
            parts = os.path.splitext(cl)[0].split('_')
            if len(parts) == 3:
                rollno, name, branch = parts[0], parts[1].upper(), parts[2].upper()
                img_path = os.path.join(root, cl)
                students_data.append({'RollNo': rollno, 'Name': name, 'Branch': branch, 'img_path': img_path})

    if not students_data:
        print('Auto-setup: No student images found to prewarm cache.')
        return False

    try:
        cache = FaceEncodingCache()
        print(f"Auto-setup: Prewarming cache for {len(students_data)} images...")
        batch_encode_and_cache(students_data, cache)
        print('Auto-setup: Prewarm complete.')
        return True
    except Exception as e:
        print('Auto-setup: Prewarm failed:', e)
        traceback.print_exc()
        return False


def train_classifiers():
    trainer = os.path.join('tools', 'train_embeddings_classifier.py')
    if not os.path.exists(trainer):
        print('Auto-setup: Trainer script not found, skipping training.')
        return False
    try:
        print('Auto-setup: Starting classifier training...')
        subprocess.run([sys.executable, trainer, '--cache', 'face_cache', '--outdir', 'models'], check=False)
        print('Auto-setup: Training finished.')
        return True
    except Exception as e:
        print('Auto-setup: Training failed:', e)
        traceback.print_exc()
        return False


def main():
    # Small delay to allow GUI to initialize
    time.sleep(1)
    print('Auto-setup: launched in background')
    ok = prewarm_cache()
    if ok:
        train_classifiers()
    else:
        print('Auto-setup: Skipping training due to prewarm failure')


if __name__ == '__main__':
    main()
