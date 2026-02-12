# register.py - Enhanced Version with Google Photos-like Duplicate Detection
import os
import shutil
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import sys
import logging

def compute_similarity_score(encodings_new, encodings_stored):
    """
    Compute a weighted similarity score between two sets of encodings using a
    Google Photos-like strategy: collect pairwise distances, use the best-K
    matches and apply decreasing weights to favor top matches.
    Returns a score in [0, 1], lower means more similar (distance).
    """
    if not encodings_new or not encodings_stored:
        return 1.0

    distances = []
    for enc_new in encodings_new:
        for enc_stored in encodings_stored:
            try:
                distance = float(face_recognition.face_distance([enc_stored], enc_new)[0])
                distances.append(distance)
            except Exception:
                continue

    if not distances:
        return 1.0

    # Sort distances and use the top matches for a more reliable score
    distances.sort()
    top_k = min(5, len(distances))  # Use up to top 5 matches

    # Weight the distances - giving more importance to the best matches
    weighted_score = 0.0
    weights_sum = 0.0
    for i in range(top_k):
        weight = 1.0 / (i + 1)  # Higher weight for better matches (i=0 -> weight=1)
        weighted_score += distances[i] * weight
        weights_sum += weight

    return (weighted_score / weights_sum) if weights_sum > 0 else 1.0
import face_recognition
try:
    from face_encoding_cache import FaceEncodingCache
    CACHING_AVAILABLE = True
except Exception:
    CACHING_AVAILABLE = False
import hashlib
import numpy as np
try:
    from tools.predict_with_classifier import load_joblib_model, predict_embedding
except Exception:
    load_joblib_model = None
    predict_embedding = None

# Classifier confidence threshold for blocking registration
REGISTER_CLASSIFIER_THRESHOLD = 0.65

# Face matching threshold - any match below 0.45 is considered a duplicate
DIRECT_MATCH_THRESHOLD = 0.45  # Strict threshold - block all matches below this
STRONG_MATCH_THRESHOLD = 0.45  # Keep same as direct match
POSSIBLE_MATCH_THRESHOLD = 0.45  # Keep same as direct match - no warnings

def _rgb_from_input(inp):
    """Normalize input into RGB numpy array. Accepts file path or BGR numpy array."""
    if isinstance(inp, str):
        if not os.path.exists(inp):
            return None
        try:
            img = face_recognition.load_image_file(inp)
            return img
        except Exception:
            return None
    else:
        arr = inp
        if arr is None:
            return None
        if len(arr.shape) == 3 and arr.shape[2] == 3:
            return cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        return arr


def align_face_by_eyes(img_rgb, landmarks):
    """Return a rotated (aligned) image where the eyes are horizontal."""
    try:
        left_eye = landmarks.get('left_eye')
        right_eye = landmarks.get('right_eye')
        if not left_eye or not right_eye:
            return img_rgb
        left_c = np.mean(left_eye, axis=0)
        right_c = np.mean(right_eye, axis=0)
        dy = right_c[1] - left_c[1]
        dx = right_c[0] - left_c[0]
        angle = np.degrees(np.arctan2(dy, dx))
        h, w = img_rgb.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img_rgb, M, (w, h), flags=cv2.INTER_CUBIC)
        return rotated
    except Exception:
        return img_rgb


def get_robust_face_encodings(img_rgb):
    """
    Generate multiple face encodings from various augmentations
    to capture the face under different conditions.
    """
    encodings = []

    # Helper to safely compute encodings and append
    def try_append(img_arr, model='large', num_jitters=2):
        try:
            enc = face_recognition.face_encodings(img_arr, model=model, num_jitters=num_jitters)
            if enc:
                encodings.append(enc[0])
        except Exception:
            return

    # 1. Original enhanced
    try:
        img_enh = cv2.convertScaleAbs(img_rgb, alpha=1.1, beta=20)
        try_append(img_enh, model='large', num_jitters=3)
    except Exception:
        pass

    # 2. Brightness variations
    for brightness in [-30, 30]:
        try:
            img_bright = cv2.convertScaleAbs(img_rgb, alpha=1.0, beta=brightness)
            try_append(img_bright, model='large', num_jitters=2)
        except Exception:
            pass

    # 3. Contrast variations
    for alpha in [0.8, 1.3]:
        try:
            img_contrast = cv2.convertScaleAbs(img_rgb, alpha=alpha, beta=0)
            try_append(img_contrast, model='large', num_jitters=2)
        except Exception:
            pass

    # 4. Alignment-based
    try:
        landmarks_list = face_recognition.face_landmarks(img_rgb)
        if landmarks_list:
            aligned = align_face_by_eyes(img_rgb, landmarks_list[0])
            try_append(aligned, model='large', num_jitters=3)
    except Exception:
        pass

    # 5. Mirrored
    try:
        mirrored = cv2.flip(img_rgb, 1)
        try_append(mirrored, model='large', num_jitters=2)
    except Exception:
        pass

    # 6. Rotated versions
    for angle in [-5, 5]:
        try:
            h, w = img_rgb.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(img_rgb, M, (w, h), flags=cv2.INTER_CUBIC)
            try_append(rotated, model='large', num_jitters=2)
        except Exception:
            pass

    # 7. Blurred
    try:
        blurred = cv2.GaussianBlur(img_rgb, (5, 5), 0)
        try_append(blurred, model='large', num_jitters=2)
    except Exception:
        pass

    # Deduplicate encodings: keep unique encodings (distance threshold)
    unique_encs = []
    try:
        for enc in encodings:
            if not unique_encs:
                unique_encs.append(enc)
                continue
            dists = face_recognition.face_distance(unique_encs, enc)
            if not any(d < 0.35 for d in dists):
                unique_encs.append(enc)
    except Exception:
        unique_encs = encodings

    return unique_encs
# compute_similarity_score is implemented above with an enhanced weighted strategy;
# the simpler minimum-distance implementation was removed to avoid duplicate definitions.


def is_face_already_registered(new_img_input):
    """
    Google Photos-like duplicate detection using multiple augmented encodings.
    Returns: (is_duplicate, min_distance, matched_file, details)
    """
    img_rgb = _rgb_from_input(new_img_input)
    if img_rgb is None:
        return False, 1.0, None, "Could not load image"
    
    # Get multiple encodings with variations
    encodings_new = get_robust_face_encodings(img_rgb)
    if not encodings_new:
        return False, 1.0, None, "No face detected in new image"
    
    images_path = 'Images_Attendance'
    if not os.path.exists(images_path):
        return False, 1.0, None, "No existing database"
    
    min_distance = 1.0
    matched_file = None
    match_details = []
    possible_matches = []  # For collecting multiple potential matches
    
    print("\n" + "="*60)
    print("CHECKING FOR DUPLICATE FACES...")
    print("="*60)
    
    # Initialize cache (if available) to speed up loading stored encodings
    cache = FaceEncodingCache() if CACHING_AVAILABLE else None

    for branch_folder in os.listdir(images_path):
        branch_dir = os.path.join(images_path, branch_folder)
        if not os.path.isdir(branch_dir):
            continue

        for img_file in os.listdir(branch_dir):
            fpath = os.path.join(branch_dir, img_file)
            try:
                stored_rgb = _rgb_from_input(fpath)
                if stored_rgb is None:
                    continue

                # Try load encoding from cache first
                encodings_stored = None
                if cache is not None:
                    parts = os.path.splitext(img_file)[0].split('_')
                    if len(parts) >= 3:
                        roll_c, name_c, branch_c = parts[0], parts[1], parts[2]
                        enc = cache.load_encoding(roll_c, name_c, branch_c, fpath)
                        if enc is not None:
                            encodings_stored = [enc]

                # If no cached encoding, compute robust encodings and save first to cache
                if not encodings_stored:
                    encodings_stored = get_robust_face_encodings(stored_rgb)
                    if encodings_stored and cache is not None and len(parts) >= 3:
                        try:
                            cache.save_encoding(roll_c, name_c, branch_c, encodings_stored[0], fpath)
                        except Exception:
                            pass

                if not encodings_stored:
                    continue

                distance = compute_similarity_score(encodings_new, encodings_stored)

                print(f"Comparing with {img_file}: distance = {distance:.4f}")

                if distance < min_distance:
                    min_distance = distance
                    matched_file = img_file

                if distance < DIRECT_MATCH_THRESHOLD:
                    match_details.append((img_file, distance))

            except Exception as e:
                print(f"Error comparing with {img_file}: {e}")
                continue
    
    print("="*60)
    
    is_duplicate = min_distance < DIRECT_MATCH_THRESHOLD
    
    if is_duplicate:
        details = f"Strong match with {matched_file} (distance: {min_distance:.4f})"
        if len(match_details) > 1:
            details += f"\n\nOther similar faces:"
            for fname, dist in sorted(match_details, key=lambda x: x[1])[:3]:
                if fname != matched_file:
                    details += f"\n  - {fname}: {dist:.4f}"
    else:
        details = f"No duplicate. Closest: {matched_file} (distance: {min_distance:.4f})"
    
    return is_duplicate, min_distance, matched_file, details


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def is_exact_image_already_present(new_img_path: str) -> bool:
    """Check if the exact same image file already exists"""
    images_path = "Images_Attendance"
    if not (new_img_path and os.path.exists(new_img_path) and os.path.exists(images_path)):
        return False
    try:
        target_hash = compute_sha256(new_img_path)
    except Exception:
        return False
    
    for branch_folder in os.listdir(images_path):
        branch_dir = os.path.join(images_path, branch_folder)
        if not os.path.isdir(branch_dir):
            continue
        for img_file in os.listdir(branch_dir):
            img_path = os.path.join(branch_dir, img_file)
            try:
                if compute_sha256(img_path) == target_hash:
                    return True
            except Exception:
                continue
    return False


def scan_registered_students():
    """Scan existing registrations and return list of dicts."""
    images_path = "Images_Attendance"
    results = []
    if not os.path.exists(images_path):
        return results
    for branch_folder in os.listdir(images_path):
        branch_dir = os.path.join(images_path, branch_folder)
        if not os.path.isdir(branch_dir):
            continue
        for img_file in os.listdir(branch_dir):
            name_no_ext = os.path.splitext(img_file)[0]
            parts = name_no_ext.split("_")
            if len(parts) != 3:
                continue
            results.append({
                'RollNo': parts[0].upper(),
                'Name': parts[1].upper(),
                'Branch': parts[2].upper(),
                'File': os.path.join(branch_dir, img_file)
            })
    return results


def register_student(root):
    reg_win = tk.Toplevel(root)
    reg_win.title("Register New Student")
    reg_win.geometry("550x500")

    tk.Label(reg_win, text="Roll No:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Label(reg_win, text="Name:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
    tk.Label(reg_win, text="Branch:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=5, sticky="e")
    tk.Label(reg_win, text="Parent Email:", font=("Arial", 10)).grid(row=3, column=0, padx=5, pady=5, sticky="e")
    tk.Label(reg_win, text="Parent Mobile 1:", font=("Arial", 10)).grid(row=4, column=0, padx=5, pady=5, sticky="e")
    tk.Label(reg_win, text="Parent Mobile 2:", font=("Arial", 10)).grid(row=5, column=0, padx=5, pady=5, sticky="e")

    roll_var, name_var = tk.StringVar(), tk.StringVar()
    parent_email_var = tk.StringVar()
    parent_mobile1_var = tk.StringVar()
    parent_mobile2_var = tk.StringVar()
    branch_var = tk.StringVar(value="CSE")
    img_path_var = tk.StringVar()

    tk.Entry(reg_win, textvariable=roll_var, width=30).grid(row=0, column=1, padx=5, pady=5)
    tk.Entry(reg_win, textvariable=name_var, width=30).grid(row=1, column=1, padx=5, pady=5)
    ttk.Combobox(reg_win, textvariable=branch_var,
                 values=['CSE', 'AIML', 'CSD', 'CAI', 'CSM'],
                 state="readonly", width=28).grid(row=2, column=1, padx=5, pady=5)
    tk.Entry(reg_win, textvariable=parent_email_var, width=30).grid(row=3, column=1, padx=5, pady=5)
    tk.Entry(reg_win, textvariable=parent_mobile1_var, width=30).grid(row=4, column=1, padx=5, pady=5)
    tk.Entry(reg_win, textvariable=parent_mobile2_var, width=30).grid(row=5, column=1, padx=5, pady=5)

    def browse_image():
        path = filedialog.askopenfilename(
            title="Select Student Photo",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png"), ("All Files", "*.*")]
        )
        if path:
            img_path_var.set(path)
            try:
                img = cv2.imread(path)
                if img is not None:
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    faces = face_recognition.face_locations(rgb_img)
                    if faces:
                        messagebox.showinfo("Face Detected", f"✓ {len(faces)} face(s) detected!")
                    else:
                        messagebox.showwarning("No Face", "⚠ No face detected. Use a clear photo.")
            except:
                pass

    def capture_image():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open camera!")
            return
            
        cv2.namedWindow("Capture Face - Press 'C' to capture, ESC to cancel")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, "Face Detected", (left, top - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.putText(frame, "Press 'C' to capture", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Press ESC to cancel", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow("Capture Face - Press 'C' to capture, ESC to cancel", frame)
            
            key = cv2.waitKey(1)
            if key == ord('c') or key == ord('C'):
                if len(face_locations) == 0:
                    messagebox.showwarning("No Face", "No face detected! Position your face clearly.")
                    continue
                elif len(face_locations) > 1:
                    messagebox.showwarning("Multiple Faces", "Multiple faces! Only one person in frame.")
                    continue
                else:
                    reg_win._captured_frame = frame.copy()
                    img_path_var.set("__IN_MEMORY_CAPTURE__")
                    messagebox.showinfo("Success", "✓ Face captured successfully!")
                    break
            elif key == 27:  # ESC
                break
        
        cap.release()
        cv2.destroyAllWindows()

    btn_frame = tk.Frame(reg_win)
    btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
    
    tk.Button(btn_frame, text="Browse Image", command=browse_image, 
             bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Capture from Webcam", command=capture_image,
             bg="#2196F3", fg="white", width=18).pack(side=tk.LEFT, padx=5)
    
    img_label = tk.Label(reg_win, textvariable=img_path_var, wraplength=400, 
                        fg="blue", font=("Arial", 9))
    img_label.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

    def save_student():
        roll = roll_var.get().strip()
        name = name_var.get().strip()
        branch = branch_var.get().strip().upper()
        img_path = img_path_var.get()
        
        if not (roll and name and branch and img_path):
            messagebox.showerror("Error", "All fields are required!")
            return
            
        in_memory = (img_path == "__IN_MEMORY_CAPTURE__")
        if not in_memory and not os.path.exists(img_path):
            messagebox.showerror("Image Missing", "Selected image not found.")
            return
        
        # Validation
        branches_list = ['CSE', 'AIML', 'CSD', 'CAI', 'CSM']
        branch_codes = {'CSD': '44', 'AIML': '61', 'CSE': '05', 'CAI': '43', 'CSM': '42'}
        valid_prefixes = ('22FE1A', '23FE5A')

        if branch not in branches_list:
            messagebox.showerror("Invalid Branch", f"Branch must be one of: {', '.join(branches_list)}")
            return

        roll_u = roll.upper()
        name_u = name.upper()
        prefix_ok = any(roll_u.startswith(p) for p in valid_prefixes)
        code_required = branch_codes.get(branch)
        code_segment = roll_u[6:8] if len(roll_u) >= 8 else ""
        
        if not (prefix_ok and code_segment == code_required):
            messagebox.showerror(
                "Invalid Roll/Branch",
                f"Roll '{roll}' doesn't match branch '{branch}'.\n\n"
                f"Valid prefixes: {', '.join(valid_prefixes)}\n"
                f"Expected code [6:8]: {code_required}\nFound: '{code_segment}'"
            )
            return

        # Check roll/name duplicates
        existing = scan_registered_students()
        if any(r['RollNo'] == roll_u for r in existing):
            messagebox.showerror("Duplicate Roll", f"Roll '{roll_u}' already registered.")
            return
        if any(r['Name'] == name_u and r['Branch'] == branch for r in existing):
            messagebox.showerror("Duplicate Name", f"Name '{name_u}' exists in {branch}.")
            return

        # Check exact image duplicate
        if (not in_memory) and is_exact_image_already_present(img_path):
            messagebox.showerror("Duplicate Image", "This exact image already exists in database.")
            return

        # Validate that the selected image contains exactly one face
        try:
            if in_memory:
                frame_bgr = getattr(reg_win, "_captured_frame", None)
                if frame_bgr is None:
                    messagebox.showerror("Image Error", "Captured image not available. Please capture again.")
                    return
                img_rgb_check = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            else:
                # Load with face_recognition for consistent color/order
                img_rgb_check = face_recognition.load_image_file(img_path)

            faces_found = face_recognition.face_locations(img_rgb_check)
            if not faces_found:
                messagebox.showerror("No Face Detected", "The selected image does not contain a detectable face. Please select/ capture a clear photo with one face.")
                return
            if len(faces_found) > 1:
                messagebox.showerror("Multiple Faces Detected", "The selected image contains multiple faces. Please provide an image with exactly one person.")
                return
        except Exception as e:
            # If face detection fails for unexpected reasons, block registration for safety
            messagebox.showerror("Face Detection Error", f"Could not validate face in the image: {e}")
            return

        # ENHANCED DUPLICATE FACE CHECK
        # First: compute robust encodings for the new image (used both by classifiers and distance checks)
        try:
            new_img_input = reg_win._captured_frame if in_memory else img_path
            encodings_new = get_robust_face_encodings(_rgb_from_input(new_img_input))
            if not encodings_new:
                messagebox.showerror("No Face", "Could not compute face encoding for the selected image.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Could not compute encodings: {e}")
            return

        # 1) Classifier-based duplicate check (if models available)
        try:
            existing = scan_registered_students()  # refresh existing list
            existing_rolls = {r['RollNo'] for r in existing}
            # Load models if present
            knn_model, knn_le = (None, None)
            svm_model, svm_le = (None, None)
            if load_joblib_model is not None:
                try:
                    knn_model, knn_le = load_joblib_model(os.path.join('models', 'knn_embeddings.joblib'))
                except Exception:
                    knn_model, knn_le = (None, None)
                try:
                    svm_model, svm_le = load_joblib_model(os.path.join('models', 'svm_embeddings.joblib'))
                except Exception:
                    svm_model, svm_le = (None, None)

            # Check each encoding produced for the new image
            for enc in encodings_new:
                if predict_embedding and knn_model is not None:
                    lbl, conf = predict_embedding(knn_model, knn_le, enc, threshold=REGISTER_CLASSIFIER_THRESHOLD)
                    if lbl is not None and lbl in existing_rolls:
                        messagebox.showerror("Duplicate Detected", f"Registration blocked: face matches existing RollNo {lbl} (confidence={conf:.2f}).")
                        return
                if predict_embedding and svm_model is not None:
                    lbl, conf = predict_embedding(svm_model, svm_le, enc, threshold=REGISTER_CLASSIFIER_THRESHOLD)
                    if lbl is not None and lbl in existing_rolls:
                        messagebox.showerror("Duplicate Detected", f"Registration blocked: face matches existing RollNo {lbl} (confidence={conf:.2f}).")
                        return
        except Exception as e:
            # Non-fatal: continue to distance-based check, but log/notify if needed
            print(f"Classifier duplicate check error: {e}")

        # 2) Distance-based duplicate check (robust comparison)
        try:
            dup, min_dist, match_file, details = is_face_already_registered(new_img_input)
            print(f"\nFace match distance: {min_dist:.4f}")  # Show distance in terminal
            if min_dist <= DIRECT_MATCH_THRESHOLD:  # Block if less than threshold
                print(f"BLOCKED: Match found with distance {min_dist:.4f} (threshold: {DIRECT_MATCH_THRESHOLD})")
                message = f"REGISTRATION BLOCKED - DUPLICATE FACE\n\n"
                message += f"Distance: {min_dist:.4f}\n"
                message += f"Matching File: {match_file}\n\n"
                message += "This face appears to already be registered."
                messagebox.showerror("Duplicate Face - Registration Blocked", message)
                return
        except Exception as e:
            print(f"Face comparison error: {e}")
            messagebox.showerror("Error", "Could not check for duplicate faces. Registration blocked for safety.")
            return
        
        # Save the image
        dest_dir = os.path.join("Images_Attendance", branch)
        os.makedirs(dest_dir, exist_ok=True)
        ext = ".jpg" if in_memory else os.path.splitext(img_path)[1]
        dest_path = os.path.join(dest_dir, f"{roll}_{name.upper()}_{branch}{ext}")

        # Prevent overwriting any existing file with same destination path
        if os.path.exists(dest_path):
            messagebox.showerror("Already Registered",
                                 "A registration with the same Roll/Name/Branch already exists. Registration aborted.")
            return
        
        try:
            if in_memory:
                frame_bgr = getattr(reg_win, "_captured_frame", None)
                if frame_bgr is None:
                    raise RuntimeError("Captured frame not available")
                cv2.imwrite(dest_path, frame_bgr)
            else:
                shutil.copy(img_path, dest_path)
            # Silent mode
            
            messagebox.showinfo("Success", 
                              f"✓ Student registered successfully!\n\n"
                              f"Roll No: {roll}\n"
                              f"Name: {name}\n"
                              f"Branch: {branch}\n\n"
                              f"Image saved to:\n{dest_path}")
            
            # Save parent contact information
            parent_email = parent_email_var.get().strip()
            parent_mobile1 = parent_mobile1_var.get().strip()
            parent_mobile2 = parent_mobile2_var.get().strip()
            
            if parent_email or parent_mobile1 or parent_mobile2:
                try:
                    import pandas as pd
                    contacts_file = 'parent_contacts.csv'
                    
                    # Check if file exists
                    if os.path.exists(contacts_file):
                        df = pd.read_csv(contacts_file)
                    else:
                        # Create new file with headers
                        df = pd.DataFrame(columns=['Roll_No', 'Student_Name', 'Parent_Email', 'Parent_Mobile1', 'Parent_Mobile2'])
                    
                    # Remove existing entry for this roll no if it exists
                    df = df[df['Roll_No'] != roll_u]
                    
                    # Add new entry
                    new_row = {
                        'Roll_No': roll_u,
                        'Student_Name': name_u,
                        'Parent_Email': parent_email,
                        'Parent_Mobile1': parent_mobile1,
                        'Parent_Mobile2': parent_mobile2
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv(contacts_file, index=False)
                    messagebox.showinfo("Success", "✓ Parent contact information saved!")
                except Exception as e:
                    messagebox.showwarning("Warning", f"Student registered but parent contact save failed: {e}")
            
            # Silent mode
            # Kick off retrain of classifiers in background (non-blocking)
            try:
                cmd = [sys.executable, os.path.join('tools', 'retrain_on_register.py')]
                subprocess.Popen(cmd)
                logging.info('Started background retrain process')
            except Exception as e:
                logging.warning('Could not start retrain process: %s', e)
            reg_win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {e}")
        finally:
            pass

    tk.Button(reg_win, text="Register Student", command=save_student, 
             bg="#FF5722", fg="white", font=("Arial", 11, "bold"),
             width=20, height=2).grid(row=8, column=0, columnspan=2, pady=20)


def dedupe_registrations() -> str:
    """Scan Images_Attendance and move duplicates (by roll, name per branch, face) to _duplicates.
    Keeps the earliest file (by modified time) as the canonical record.
    Returns a summary string of actions.
    """
    images_path = "Images_Attendance"
    if not os.path.exists(images_path):
        return "No Images_Attendance folder found."

    duplicates_dir = os.path.join(images_path, "_duplicates")
    os.makedirs(duplicates_dir, exist_ok=True)

    # Collect entries
    entries = []
    for branch_folder in os.listdir(images_path):
        branch_dir = os.path.join(images_path, branch_folder)
        if not os.path.isdir(branch_dir) or branch_folder == "_duplicates":
            continue
        for img_file in os.listdir(branch_dir):
            file_path = os.path.join(branch_dir, img_file)
            if not os.path.isfile(file_path):
                continue
            name_no_ext = os.path.splitext(img_file)[0]
            parts = name_no_ext.split("_")
            if len(parts) != 3:
                continue
            roll_u, name_u, branch_u = parts[0].upper(), parts[1].upper(), parts[2].upper()
            entries.append({
                'RollNo': roll_u,
                'Name': name_u,
                'Branch': branch_u,
                'File': file_path,
                'Mtime': os.path.getmtime(file_path)
            })

    actions = []

    # 1) Duplicate RollNo (global)
    by_roll = {}
    for e in entries:
        by_roll.setdefault(e['RollNo'], []).append(e)
    for roll, group in by_roll.items():
        if len(group) <= 1:
            continue
        group_sorted = sorted(group, key=lambda x: x['Mtime'])
        for dup in group_sorted[1:]:
            dest = os.path.join(duplicates_dir, os.path.basename(dup['File']))
            try:
                shutil.move(dup['File'], dest)
                actions.append(f"Moved duplicate RollNo {roll}: {dup['File']} -> {dest}")
            except Exception as ex:
                actions.append(f"Failed moving duplicate RollNo {roll}: {dup['File']} ({ex})")

    # Refresh entries after moves
    entries = [e for e in entries if os.path.exists(e['File'])]

    # 2) Duplicate Name within Branch
    by_branch_name = {}
    for e in entries:
        key = (e['Branch'], e['Name'])
        by_branch_name.setdefault(key, []).append(e)
    for (branch_u, name_u), group in by_branch_name.items():
        if len(group) <= 1:
            continue
        group_sorted = sorted(group, key=lambda x: x['Mtime'])
        for dup in group_sorted[1:]:
            if not os.path.exists(dup['File']):
                continue
            dest = os.path.join(duplicates_dir, os.path.basename(dup['File']))
            try:
                shutil.move(dup['File'], dest)
                actions.append(f"Moved duplicate Name {name_u} in {branch_u}: {dup['File']} -> {dest}")
            except Exception as ex:
                actions.append(f"Failed moving duplicate Name {name_u} in {branch_u}: {dup['File']} ({ex})")

    # Refresh entries again
    entries = [e for e in entries if os.path.exists(e['File'])]

    # 3) Near-duplicate faces (same person different files)
    file_to_encoding = {}

    def load_encoding(img_path: str):
        try:
            img = face_recognition.load_image_file(img_path)
            img_enh = cv2.convertScaleAbs(img, alpha=1.1, beta=20)
            enc = face_recognition.face_encodings(img_enh, model="large", num_jitters=1)
            if not enc:
                enc = face_recognition.face_encodings(img, model="small", num_jitters=1)
            return enc[0] if enc else None
        except Exception:
            return None

    for e in entries:
        if os.path.exists(e['File']):
            file_to_encoding[e['File']] = load_encoding(e['File'])

    by_branch = {}
    for e in entries:
        if os.path.exists(e['File']):
            by_branch.setdefault(e['Branch'], []).append(e)

    FACE_DUP_THRESHOLD = 0.40
    for branch_u, group in by_branch.items():
        group_sorted = sorted(group, key=lambda x: x['Mtime'])
        kept_files = set()
        for i in range(len(group_sorted)):
            a = group_sorted[i]
            if not os.path.exists(a['File']):
                continue
            if a['File'] in kept_files:
                continue
            enc_a = file_to_encoding.get(a['File'])
            if enc_a is None:
                dest = os.path.join(duplicates_dir, os.path.basename(a['File']))
                try:
                    shutil.move(a['File'], dest)
                    actions.append(f"Moved no-face file: {a['File']} -> {dest}")
                except Exception as ex:
                    actions.append(f"Failed moving no-face file: {a['File']} ({ex})")
                continue
            kept_files.add(a['File'])
            for j in range(i + 1, len(group_sorted)):
                b = group_sorted[j]
                if not os.path.exists(b['File']):
                    continue
                enc_b = file_to_encoding.get(b['File'])
                if enc_b is None:
                    dest = os.path.join(duplicates_dir, os.path.basename(b['File']))
                    try:
                        shutil.move(b['File'], dest)
                        actions.append(f"Moved no-face file: {b['File']} -> {dest}")
                    except Exception as ex:
                        actions.append(f"Failed moving no-face file: {b['File']} ({ex})")
                    continue
                dist_val = float(face_recognition.face_distance([enc_a], enc_b)[0])
                if dist_val < FACE_DUP_THRESHOLD:
                    dest = os.path.join(duplicates_dir, os.path.basename(b['File']))
                    try:
                        shutil.move(b['File'], dest)
                        actions.append(f"Moved duplicate Face (dist {dist_val:.3f}): {b['File']} -> {dest}")
                    except Exception as ex:
                        actions.append(f"Failed moving duplicate Face: {b['File']} ({ex})")

    if not actions:
        return "No duplicates found."
    return "\n".join(actions)
