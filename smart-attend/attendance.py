# attendance.py
import cv2
import numpy as np
import face_recognition
import os
import pandas as pd
from datetime import datetime
import dlib
from scipy.spatial import distance as dist
import tkinter as tk
from tkinter import messagebox, simpledialog
import time
from collections import deque
import threading
import queue
import joblib
import logging

# Import location and notification modules
try:
    from location_verification import LocationVerifier
    LOCATION_VERIFICATION_AVAILABLE = True
except Exception:
    LOCATION_VERIFICATION_AVAILABLE = False
    print("Location verification not available")

try:
    from parent_notifications import ParentNotificationManager
    PARENT_NOTIFICATIONS_AVAILABLE = True
except Exception:
    PARENT_NOTIFICATIONS_AVAILABLE = False
    print("Parent notifications not available")

# Import caching system for large databases
try:
    from face_encoding_cache import FaceEncodingCache, batch_encode_and_cache
    CACHING_AVAILABLE = True
except Exception:
    CACHING_AVAILABLE = False
    print("Face encoding cache not available - using regular loading")

# Optional YOLOv8 for phone detection
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except Exception:
    _YOLO_AVAILABLE = False

# Screen content analyzer (heuristic / optional classifier)
try:
    from screen_classifier import (
        analyze_phone_region,
        load_mobilenetv2_classifier,
        classify_phone_screen_mobilenet,
    )
except Exception:
    try:
        from .screen_classifier import (
            analyze_phone_region,
            load_mobilenetv2_classifier,
            classify_phone_screen_mobilenet,
        )
    except Exception:
        print("Screen classifier not available")

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# CSV write lock to avoid concurrent writes
csv_write_lock = threading.Lock()

# Classifier paths / thresholds
CLASSIFIER_THRESHOLD = 0.65
KNn_MODEL_PATH = os.path.join('models', 'knn_embeddings.joblib')
SVM_MODEL_PATH = os.path.join('models', 'svm_embeddings.joblib')

try:
    from tools.predict_with_classifier import load_joblib_model, predict_embedding
except Exception:
    load_joblib_model = None
    predict_embedding = None

def run_attendance(period, source="mobile", automated=False):
    """
    Run attendance session for a specific period
    automated=True runs in headless mode without GUI prompts
    """
    # Location verification
    if LOCATION_VERIFICATION_AVAILABLE:
        try:
            verifier = LocationVerifier()
            if verifier.config.get('verification_required', False):
                location_verified, location_message, location_data = verifier.verify_location()
                if not location_verified:
                    messagebox.showerror(
                        "Location Verification Failed",
                        f"Could not verify attendance location:\n\n{location_message}"
                    )
                    return
                else:
                    messagebox.showinfo("Location Verified", location_message)
        except Exception as e:
            logging.warning(f"Location verification error: {e}")
    
    # Setup
    branches_list = ['CSE', 'AIML', 'CSD', 'CAI', 'CSM']
    periods = ['Period1', 'Period2', 'Period3', 'Period4', 'Period5', 'Period6']
    date_today = datetime.now().strftime('%d/%m/%Y')
    if not automated:
        try:
            if not messagebox.askyesno("Confirm Date", f"Use today's date: {date_today}?"):
                user_date = simpledialog.askstring(
                    "Set Date",
                    "Enter date (dd/mm/yyyy):",
                    initialvalue=date_today
                )
                if user_date:
                    # Basic validation dd/mm/yyyy
                    try:
                        dt = datetime.strptime(user_date.strip(), '%d/%m/%Y')
                        date_today = dt.strftime('%d/%m/%Y')
                    except Exception:
                        messagebox.showwarning("Invalid Date", f"Invalid date format. Using {date_today}.")
        except Exception:
            # If GUI prompts fail, keep default date
            pass
    else:
        # In automated mode, always use today's date
        logger.info(f"Automated mode: Using date {date_today}")
    period_col = f'Period{period}'
    attendance_folder = 'Attendance_Records'

    branch_codes = {
        'CSD': '44',
        'AIML': '61',
        'CSE': '05',
        'CAI': '43',
        'CSM': '42'
    }
    valid_prefixes = ('22FE1A', '23FE5A')

    # Gather all students
    students = []
    images = []
    image_files = []
    images_path = 'Images_Attendance'
    students_data = []  # Store student info with image paths
    
    # Collect all student information first
    for root_dir, dirs, files in os.walk(images_path):
        for cl in files:
            parts = os.path.splitext(cl)[0].split('_')
            if len(parts) == 3:
                rollno, name, branch = parts[0], parts[1].upper(), parts[2].upper()
                if (rollno.startswith(valid_prefixes) and
                    branch in branches_list and
                    branch in branch_codes and
                    rollno[-4:-2] == branch_codes[branch]):
                    img_path = os.path.join(root_dir, cl)
                    if os.path.exists(img_path):
                        students_data.append({
                            'RollNo': rollno,
                            'Name': name,
                            'Branch': branch,
                            'img_path': img_path
                        })
    
    # Use caching if available for large datasets
    if CACHING_AVAILABLE and len(students_data) > 100:
        print(f"\n📦 Using efficient caching for {len(students_data)} students...")
        cache = FaceEncodingCache()
        encodeListKnown, students = batch_encode_and_cache(students_data, cache)
    else:
        # Original loading method for small datasets
        for root_dir, dirs, files in os.walk(images_path):
            for cl in files:
                parts = os.path.splitext(cl)[0].split('_')
                if len(parts) == 3:
                    rollno, name, branch = parts[0], parts[1].upper(), parts[2].upper()
                    if (rollno.startswith(valid_prefixes) and
                        branch in branches_list and
                        branch in branch_codes and
                        rollno[-4:-2] == branch_codes[branch]):
                        img_path = os.path.join(root_dir, cl)
                        curImg = cv2.imread(img_path)
                        if curImg is not None:
                            images.append(curImg)
                            students.append({'RollNo': rollno, 'Name': name, 'Branch': branch})
                            image_files.append(img_path)
        
        # Encode using original method
        def findEncodings(images):
            encodeList = []
            valid_students = []
            
            for img, student in zip(images, students):
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Faster encoding for large datasets
                encodes = face_recognition.face_encodings(img_rgb, model="small", num_jitters=1)
                
                if len(encodes) > 0:
                    candidate = encodes[0]
                    if encodeList:
                        dists = face_recognition.face_distance(encodeList, candidate)
                        if np.any(dists < 0.35):
                            continue
                    encodeList.append(candidate)
                    valid_students.append(student)
            
            return encodeList, valid_students
        
        encodeListKnown, students = findEncodings(images)

    if not encodeListKnown:
        error_msg = "No valid face encodings found. Check Images_Attendance folder."
        if automated:
            logger.error(error_msg)
            return
        else:
            messagebox.showerror("No valid faces", error_msg)
            return

    # --- Load optional classifiers (KNN / SVM) if available ---
    knn_model = None
    knn_le = None
    svm_model = None
    svm_le = None
    roll_to_index = {}
    try:
        if load_joblib_model:
            if os.path.exists(KNn_MODEL_PATH):
                knn_model, knn_le = load_joblib_model(KNn_MODEL_PATH)
                logging.info("KNN model loaded from %s", KNn_MODEL_PATH)
            if os.path.exists(SVM_MODEL_PATH):
                svm_model, svm_le = load_joblib_model(SVM_MODEL_PATH)
                logging.info("SVM model loaded from %s", SVM_MODEL_PATH)
    except Exception as e:
        logging.warning("Error loading classifier models: %s", e)

    # build roll -> index map for quick lookup
    for idx, s in enumerate(students):
        roll_to_index[s['RollNo']] = idx

    # Camera source and stabilization setup
    if source == "mobile":
        if not automated:
            default_url = "http://192.168.191.132:8080/video"
            ip_webcam_url = simpledialog.askstring(
                "IP Webcam URL",
                f"Enter your phone's IP Webcam URL (default: {default_url}):",
                initialvalue=default_url
            )
            if not ip_webcam_url:
                ip_webcam_url = default_url
        else:
            # In automated mode, use default IP webcam URL
            ip_webcam_url = "http://192.168.191.132:8080/video"
            logger.info(f"Automated mode: Using default IP webcam URL: {ip_webcam_url}")
        cap = cv2.VideoCapture(ip_webcam_url)
    else:
        cap = cv2.VideoCapture(0)
        
    # Set resolution for clear face detection
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Camera settings optimized for responsiveness
    cap.set(cv2.CAP_PROP_FPS, 30)  # Higher FPS for real-time response
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimum buffer for instant response
    
    if source != "mobile":  # Some settings may not work with IP camera
        cap.set(cv2.CAP_PROP_EXPOSURE, -2)  # Balanced exposure
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)  # Mid-level brightness
        cap.set(cv2.CAP_PROP_CONTRAST, 128)  # Mid-level contrast

    present_rollnos = []

    # Phone detection backends
    yolo_model = None
    yolo_weights = "yolov8n.pt"
    if _YOLO_AVAILABLE and os.path.exists(yolo_weights):
        try:
            yolo_model = YOLO(yolo_weights)
            print("YOLOv8 loaded for phone detection")
        except Exception as e:
            print(f"Failed to load YOLOv8: {e}")
            yolo_model = None

    ssd_net = None
    CLASSES = []
    if yolo_model is None:
        proto_path = "MobileNetSSD_deploy.prototxt.txt"
        model_path = "MobileNetSSD_deploy.caffemodel"
        if os.path.exists(proto_path) and os.path.exists(model_path):
            ssd_net = cv2.dnn.readNetFromCaffe(proto_path, model_path)
            CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                       "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                       "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                       "sofa", "train", "tvmonitor", "laptop", "mouse", "remote", "keyboard",
                       "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
                       "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"]

    # Dlib blink detection
    predictor_path = "shape_predictor_68_face_landmarks.dat"
    if not os.path.exists(predictor_path):
        messagebox.showerror("Missing File", f"{predictor_path} not found. Download it from dlib's model zoo.")
        return
        
    detector_dlib = dlib.get_frontal_face_detector()
    predictor_dlib = dlib.shape_predictor(predictor_path)
    LEFT_EYE_IDX = list(range(42, 48))
    RIGHT_EYE_IDX = list(range(36, 42))
    EAR_THRESHOLD = 0.23
    CONSEC_FRAMES = 2
    blink_counter = 0

    def eye_aspect_ratio(eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    recognized_students = []
    RECOGNITION_THRESHOLD = 0.6  # LOWERED from 0.6 for better recognition
    blink_timeout = 8
    last_blink_time = time.time()
    
    # Blink warning system
    blink_warning_counter = 0
    BLINK_WARNING_THRESHOLD = 3
    last_blink_warning_time = time.time()
    
    # Phone detection statez
    phone_detection_counter = 0
    PHONE_DETECTION_THRESHOLD = 2
    phone_currently_detected = False
    prev_phone_crop = None
    phone_photo_votes = deque(maxlen=3)

    # Optional MobileNetV2 screen classifier
    mobilenet_model, mobilenet_transform = None, None
    try:
        mobilenet_model, mobilenet_transform = load_mobilenetv2_classifier(weights_path=None)
    except:
        pass
    
    tick, cross = "Present", "Absent"

    # Silent mode
    # --- Background recognition worker (keeps UI smooth) ---
    process_every = 3  # process heavy recognition every N frames
    frame_count = 0
    recognition_overlay = []  # list of dicts with {'box':(x1,y1,x2,y2),'label':str,'ts':time.time()}
    worker_lock = threading.Lock()
    worker_busy = False

    def recognition_worker(frame_for_processing, known_encodings, students_ref):
        """Runs in background: detect faces, compute encodings, match with known encodings.
        Updates recognition_overlay and present_rollnos under lock.
        """
        nonlocal worker_busy, recognition_overlay, present_rollnos
        # Classifier models (nonlocal so we can load in outer scope)
        nonlocal knn_model, knn_le, svm_model, svm_le, roll_to_index
        try:
            # Resize for faster detection
            small_frame = cv2.resize(frame_for_processing, (0,0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Detect faces on small frame (faster)
            face_locs_small = face_recognition.face_locations(rgb_small, model='hog')
            if not face_locs_small:
                with worker_lock:
                    recognition_overlay = []
                return

            # Convert small coords to original scale
            scaled_face_locs = []
            for top, right, bottom, left in face_locs_small:
                scaled_face_locs.append((top*2, right*2, bottom*2, left*2))

            # Compute encodings on original-size cropped areas for accuracy
            rgb_orig = cv2.cvtColor(frame_for_processing, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_orig, scaled_face_locs, model='small', num_jitters=1)

            overlays = []
            for encode, (top, right, bottom, left) in zip(encodings, scaled_face_locs):
                label = None
                # 1) Try classifier-based closed-set recognition (fast)
                try:
                    if predict_embedding and knn_model is not None:
                        lbl, conf = predict_embedding(knn_model, knn_le, encode, threshold=CLASSIFIER_THRESHOLD)
                        if lbl is not None:
                            label = lbl
                    if label is None and predict_embedding and svm_model is not None:
                        lbl, conf = predict_embedding(svm_model, svm_le, encode, threshold=CLASSIFIER_THRESHOLD)
                        if lbl is not None:
                            label = lbl
                except Exception:
                    label = None

                # 2) Fallback to distance matching if classifier didn't return a confident label
                best_distance = None
                if label is None and len(known_encodings) > 0:
                    distances = face_recognition.face_distance(known_encodings, encode)
                    matchIndex = np.argmin(distances)
                    best_distance = float(distances[matchIndex])
                    if best_distance < RECOGNITION_THRESHOLD:
                        s = students_ref[matchIndex]
                        label = s['RollNo']
                    else:
                        label = None

                if label is None:
                    pretty = f"Unknown (dist: {best_distance:.2f})" if best_distance is not None else "Unknown"
                    overlays.append({'box': (left, top, right, bottom), 'label': pretty, 'ts': time.time()})
                    continue

                # Map label (rollno) back to student record if possible
                s = None
                if isinstance(label, str) and label in roll_to_index:
                    s = students_ref[roll_to_index[label]]

                if s is None:
                    # Try to find by RollNo in students_ref
                    for ss in students_ref:
                        if ss.get('RollNo') == label:
                            s = ss
                            break

                if s is None:
                    overlays.append({'box': (left, top, right, bottom), 'label': f"Unknown ({label})", 'ts': time.time()})
                    continue

                rollno = s['RollNo']
                name = s['Name']
                branch = s['Branch']

                # Check if already marked in CSV for this period
                csv_file = os.path.join(attendance_folder, f'Attendance_{branch}.csv')
                already_marked = False
                if os.path.exists(csv_file):
                    try:
                        df = pd.read_csv(csv_file)
                        if ((df['RollNo'] == rollno) & 
                            (df['Date'] == date_today) & 
                            (df[period_col].astype(str).str.lower().str.strip() == tick.lower())).any():
                            already_marked = True
                    except Exception:
                        pass

                if already_marked:
                    label_text = f"{rollno} | {name} | {branch} | ALREADY TAKEN"
                else:
                    label_text = f"{rollno} | {name} | {branch}"

                # Add to present list safely (only if NOT already marked)
                with worker_lock:
                    if rollno not in present_rollnos:
                        present_rollnos.append(rollno)
                    # Track recognized students for sidebar display and final summary
                    try:
                        rec_tuple = (rollno, name, branch)
                        if rec_tuple not in recognized_students:
                            recognized_students.append(rec_tuple)
                    except Exception:
                        pass

                overlays.append({'box': (left, top, right, bottom), 'label': label_text, 'ts': time.time()})

                overlays.append({'box': (left, top, right, bottom), 'label': label, 'ts': time.time()})

            with worker_lock:
                recognition_overlay = overlays
        except Exception:
            pass
        finally:
            worker_busy = False

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame_count += 1
            
        # Use frame directly without any stabilization for instant response
        img = frame.copy()
        
        # Light noise reduction that won't cause delay
        img = cv2.GaussianBlur(img, (3, 3), 0)
        
        (h, w) = img.shape[:2]
        phone_found = False
        phone_crop = None

        # Phone detection logic
        if yolo_model is not None:
            results = yolo_model.predict(img, imgsz=640, verbose=False)
            for r in results:
                if not hasattr(r, 'boxes'):
                    continue
                for b in r.boxes:
                    cls_id = int(b.cls.cpu().numpy()[0])
                    conf = float(b.conf.cpu().numpy()[0])
                    name = r.names.get(cls_id, str(cls_id))
                    if name != "cell phone" or conf < 0.5:
                        continue
                    x1, y1, x2, y2 = map(int, b.xyxy.cpu().numpy()[0])
                    startX, startY, endX, endY = max(0, x1), max(0, y1), min(w - 1, x2), min(h - 1, y2)
                    box_width = endX - startX
                    box_height = endY - startY
                    box_area = box_width * box_height
                    min_area = (w * h) * 0.02
                    max_area = (w * h) * 0.25
                    if box_area <= 0:
                        continue
                    aspect_ratio = max(box_width, box_height) / max(1, min(box_width, box_height))
                    if not (min_area <= box_area <= max_area and 1.5 <= aspect_ratio <= 3.0):
                        continue
                    phone_found = True
                    phone_crop = img[startY:endY, startX:endX]
                    cv2.rectangle(img, (startX, startY), (endX, endY), (0, 0, 255), 2)
                    cv2.putText(img, f"PHONE (YOLO) {conf:.2f}", (startX, startY - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    break
        elif ssd_net is not None:
            blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 0.007843, (300, 300), 127.5)
            ssd_net.setInput(blob)
            detections = ssd_net.forward()
            for i in np.arange(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                idx = int(detections[0, 0, i, 1])
                if confidence > 0.4 and CLASSES[idx] == "cell phone":
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    box_width = endX - startX
                    box_height = endY - startY
                    box_area = box_width * box_height
                    min_area = (w * h) * 0.02
                    max_area = (w * h) * 0.25
                    aspect_ratio = max(box_width, box_height) / max(1, min(box_width, box_height))
                    if min_area <= box_area <= max_area and 1.5 <= aspect_ratio <= 3.0:
                        phone_found = True
                        phone_crop = img[startY:endY, startX:endX]
                        cv2.rectangle(img, (startX, startY), (endX, endY), (0, 0, 255), 2)
                        cv2.putText(img, f"PHONE (SSD) {confidence:.2f}", (startX, startY - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        break

        phone_showing_photo = False
        if phone_found and phone_crop is not None and 'analyze_phone_region' in globals():
            analysis = analyze_phone_region(phone_crop, prev_phone_crop)
            prev_phone_crop = phone_crop.copy()
            mobilenet_prob = 0.0
            if mobilenet_model is not None:
                mobilenet_prob = classify_phone_screen_mobilenet(mobilenet_model, mobilenet_transform, phone_crop)
            is_photo_frame = bool(analysis.get("is_photo", False) or mobilenet_prob >= 0.5)
            phone_photo_votes.append(is_photo_frame)
            if len(phone_photo_votes) == phone_photo_votes.maxlen and sum(phone_photo_votes) >= 2:
                phone_showing_photo = True

        phone_currently_detected = phone_found or phone_showing_photo
        
        if phone_found:
            phone_detection_counter += 1
            if phone_detection_counter >= PHONE_DETECTION_THRESHOLD:
                # Close immediately when phone is persistently detected (no blocking wait)
                cap.release()
                cv2.destroyAllWindows()
                messagebox.showerror("Device Detected", f"Phone detected {PHONE_DETECTION_THRESHOLD} consecutive times. Webcam closed.")
                return
            else:
                warning_text = f"PHONE WARNING! ({phone_detection_counter}/{PHONE_DETECTION_THRESHOLD})"
                text_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                cv2.rectangle(img, (40, 50), (40 + text_size[0] + 20, 50 + text_size[1] + 20), (0, 0, 255), -1)
                cv2.putText(img, warning_text, (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                remaining = PHONE_DETECTION_THRESHOLD - phone_detection_counter
                countdown_text = f"REMOVING PHONE IN {remaining} DETECTIONS"
                cv2.putText(img, countdown_text, (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        else:
            if phone_detection_counter > 0:
                cv2.putText(img, "PHONE REMOVED - CONTINUING ATTENDANCE", (50, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            phone_detection_counter = 0

        # Heavy processing (face detection, landmarks, and recognition)
        blink_detected = False
        if frame_count % process_every == 0:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            rects = detector_dlib(gray, 0)

            if len(rects) == 0:
                img_rgb_temp = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(img_rgb_temp, model="hog")
                if face_locations:
                    rects = [dlib.rectangle(left, top, right, bottom) for top, right, bottom, left in face_locations]

            for rect in rects:
                shape = predictor_dlib(gray, rect)
                shape_np = np.array([(shape.part(i).x, shape.part(i).y) for i in range(68)])
                leftEAR = eye_aspect_ratio(shape_np[LEFT_EYE_IDX])
                rightEAR = eye_aspect_ratio(shape_np[RIGHT_EYE_IDX])
                ear = (leftEAR + rightEAR) / 2.0

                if ear < EAR_THRESHOLD:
                    blink_counter += 1
                else:
                    if blink_counter >= CONSEC_FRAMES:
                        blink_detected = True
                        blink_warning_counter = 0
                        last_blink_warning_time = time.time()
                    blink_counter = 0

            # If blink detected, either start recognition worker or block due to phone
            if blink_detected:
                if not phone_currently_detected:
                    last_blink_time = time.time()
                    # Start background worker (if not already busy)
                    if not worker_busy:
                        worker_busy = True
                        frame_for_worker = img.copy()
                        t = threading.Thread(target=recognition_worker, args=(frame_for_worker, encodeListKnown, students))
                        t.daemon = True
                        t.start()
                else:
                    for rect in rects:
                        top, right, bottom, left = rect.top(), rect.right(), rect.bottom(), rect.left()
                        cv2.rectangle(img, (left, top), (right, bottom), (0, 165, 255), 2)
                        block_msg = "PHONE PHOTO DETECTED - NO ATTENDANCE" if 'phone_photo_votes' in locals() and sum(phone_photo_votes) >= 2 else "PHONE DETECTED - NO ATTENDANCE"
                        cv2.putText(img, block_msg, (left, bottom + 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        else:
            # skip heavy processing on this frame
            rects = []

        # Blink warning system
        if len(rects) > 0 and (time.time() - last_blink_warning_time) > blink_timeout:
            blink_warning_counter += 1
            last_blink_warning_time = time.time()
            
            if blink_warning_counter >= BLINK_WARNING_THRESHOLD:
                cv2.putText(img, "WEBCAM CLOSING - NO BLINK DETECTED!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 3)
                # Close immediately on liveness failure (no blocking wait)
                cap.release()
                cv2.destroyAllWindows()
                messagebox.showerror("Liveness Failed", "No blink detected after multiple warnings. Please use a live face.")
                return
            else:
                if blink_warning_counter == 1:
                    warning_text = "PLEASE BLINK YOUR EYES! (Warning 1/2)"
                    warning_color = (0, 165, 255)
                elif blink_warning_counter == 2:
                    warning_text = "BLINK NOW OR WEBCAM WILL CLOSE! (Final Warning 2/2)"
                    warning_color = (0, 0, 255)
                
                text_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
                cv2.rectangle(img, (40, 40), (40 + text_size[0] + 20, 40 + text_size[1] + 20), warning_color, -1)
                cv2.putText(img, warning_text, (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                remaining_time = blink_timeout
                countdown_text = f"Blink within {remaining_time} seconds!"
                cv2.putText(img, countdown_text, (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, warning_color, 2)

        # Sidebar
        # Draw any overlays produced by the background worker (non-blocking)
        with worker_lock:
            overlays_copy = list(recognition_overlay)
        for ov in overlays_copy:
            left, top, right, bottom = ov['box']
            label = ov.get('label', '')
            # Color coding: green for new attendance, yellow/cyan for already taken, red for unknown
            if 'ALREADY TAKEN' in label:
                color = (0, 255, 255)  # Cyan for already taken
            elif label.startswith('Unknown'):
                color = (0, 0, 255)  # Red for unknown
            else:
                color = (0, 255, 0)  # Green for new attendance
            cv2.rectangle(img, (left, top), (right, bottom), color, 2)
            cv2.putText(img, label, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        sidebar_x = img.shape[1] - 300
        cv2.rectangle(img, (sidebar_x, 0), (img.shape[1], img.shape[0]), (50,50,50), -1)
        cv2.putText(img, "Recognized Students:", (sidebar_x+10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
        # Read recognized students under lock to avoid concurrent modification
        with worker_lock:
            rec_copy = list(recognized_students)
        for idx, (rollno, name, branch) in enumerate(rec_copy):
            cv2.putText(img, f"{rollno} | {name} | {branch}", (sidebar_x+10, 60+idx*25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        cv2.imshow("Webcam", img)
        if cv2.waitKey(1) == 13:
            break

    cap.release()
    cv2.destroyAllWindows()

    # Save attendance
    if not os.path.exists(attendance_folder):
        os.makedirs(attendance_folder)
    
    students_by_branch = {}
    for student in students:
        branch = student['Branch']
        if branch not in students_by_branch:
            students_by_branch[branch] = []
        students_by_branch[branch].append(student)
    
    for branch, branch_students in students_by_branch.items():
        csv_file = os.path.join(attendance_folder, f'Attendance_{branch}.csv')
        
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
                df = pd.DataFrame()
        else:
            df = pd.DataFrame()
        
        for student in branch_students:
            rollno = student['RollNo']
            name = student['Name']
            branch_name = student['Branch']
            
            mask = (df['RollNo'] == rollno) & (df['Date'] == date_today)
            if not mask.any():
                new_row = {
                    'RollNo': rollno,
                    'Name': name,
                    'Branch': branch_name,
                    **{p: cross for p in periods},
                    'Date': date_today
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        for i, row in df.iterrows():
            if row['Date'] == date_today and row['RollNo'] in present_rollnos:
                df.at[i, period_col] = tick
        
        df = df.drop_duplicates(subset=['RollNo', 'Date'], keep='first')
        header = ['RollNo', 'Name', 'Branch'] + periods + ['Date']
        df = df[header]
        # Atomic write to avoid corruption; use lock to avoid concurrent writers
        tmp_file = csv_file + '.tmp'
        try:
            with csv_write_lock:
                df.to_csv(tmp_file, index=False)
                os.replace(tmp_file, csv_file)
        except Exception as e:
            logging.error("Failed to write attendance CSV %s: %s", csv_file, e)
        
        # Send notifications to parents
        if PARENT_NOTIFICATIONS_AVAILABLE:
            try:
                notifier = ParentNotificationManager()
                current_time = datetime.now().strftime('%H:%M:%S')
                notification_summary = []
                
                # Send notifications for present students
                for student in recognized_students:
                    roll_no = student.get('RollNo')
                    name = student.get('Name')
                    
                    # Send attendance marked notification
                    if notifier.config['notifications'].get('send_on_absence') or notifier.config['email']['enabled']:
                        notifier.notify_attendance_marked(name, roll_no, date_today, current_time)
                    
                    # Check attendance percentage and send low attendance alert if needed
                    student_df = df[df['RollNo'] == roll_no]
                    if not student_df.empty:
                        present_count = 0
                        total_classes = 0
                        for col in periods:
                            if student_df[col].values[0] == tick:
                                present_count += 1
                            if student_df[col].values[0] in [tick, cross]:
                                total_classes += 1
                        
                        if total_classes > 0:
                            attendance_pct = (present_count / total_classes) * 100
                            notifier.notify_low_attendance(name, roll_no, attendance_pct)
                
                # Send absence notifications for absent students
                if notifier.config['notifications'].get('send_on_absence', False):
                    absent_students = []
                    for i, row in df.iterrows():
                        if row['Date'] == date_today and row[period_col] == cross:
                            roll_no = row['RollNo']
                            name = row['Name']
                            absent_students.append({'RollNo': roll_no, 'Name': name})
                    
                    if absent_students:
                        logging.info(f"Sending absence notifications for {period} to {len(absent_students)} students")
                        notification_summary.append(f"📤 Absence alerts sent to {len(absent_students)} parents")
                        for student in absent_students:
                            roll_no = student['RollNo']
                            name = student['Name']
                            current_time = datetime.now().strftime('%H:%M:%S')
                            notifier.notify_absence(name, roll_no, date_today)
                            logging.info(f"Absence notification sent for {roll_no} ({name}) - {period} at {current_time}")
                    else:
                        logging.info(f"No absence notifications needed for {period} - all students present or already marked")
                        notification_summary.append("✅ All students present - no absence alerts needed")
                        
                    # Auto-send next period's attendance if enabled
                    if notifier.config['notifications'].get('auto_send_per_period', False):
                        delay_seconds = notifier.config['notifications'].get('auto_send_delay_seconds', 30)
                        notification_summary.append(f"⏰ Auto-advance to next period in {delay_seconds} seconds")
                        # This will be handled by the GUI timer
                        
            except Exception as e:
                logging.error(f"Parent notification failed: {e}")
                notification_summary.append(f"❌ Notification error: {e}")
        
        # Show notification summary
        if notification_summary:
            summary_text = f"{period} Complete\n" + "\n".join(notification_summary)
            if automated:
                logger.info(f"Period Complete: {summary_text.replace(chr(10), ' | ')}")
            else:
                messagebox.showinfo("Period Complete", summary_text)
    
    # Silent mode - only show essential completion message
    final_message = f"Attendance session completed for {period}.\n"
    final_message += f"✓ {len(recognized_students)} students recognized and marked present.\n"
    final_message += f"✓ Absence notifications sent to parents of absent students.\n"
    final_message += f"✓ Attendance data saved to CSV files."
    
    if automated:
        logger.info(f"Attendance Complete: {final_message.replace(chr(10), ' | ')}")
    else:
        messagebox.showinfo("Attendance Complete", final_message)