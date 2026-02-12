# face_encoding_cache.py
# Efficient face encoding caching system for handling large student databases
import os
import pickle
import json
import cv2
import face_recognition
import numpy as np
from datetime import datetime
import hashlib

class FaceEncodingCache:
    """Cache face encodings to disk for faster loading with large datasets"""
    
    def __init__(self, cache_dir='face_cache'):
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(cache_dir, 'metadata.json')
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_file_hash(self, filepath):
        """Get hash of image file to detect changes"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def get_cache_filename(self, rollno, name, branch):
        """Generate cache filename from student info"""
        return f"{rollno}_{name}_{branch}.pkl"
    
    def save_encoding(self, rollno, name, branch, encoding, img_path):
        """Save face encoding to cache"""
        try:
            cache_file = os.path.join(self.cache_dir, self.get_cache_filename(rollno, name, branch))
            file_hash = self.get_file_hash(img_path)
            
            cache_data = {
                'schema_version': 1,
                'rollno': rollno,
                'name': name,
                'branch': branch,
                'encoding': encoding,
                'file_hash': file_hash,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            return True
        except Exception as e:
            print(f"Error saving cache for {rollno}: {e}")
            return False
    
    def load_encoding(self, rollno, name, branch, img_path):
        """Load encoding from cache if valid, otherwise return None"""
        try:
            cache_file = os.path.join(self.cache_dir, self.get_cache_filename(rollno, name, branch))
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # If schema_version absent, treat as old format (0)
            schema = cache_data.get('schema_version', 0)
            # Verify file hasn't changed
            current_hash = self.get_file_hash(img_path)
            if cache_data.get('file_hash') != current_hash:
                return None  # File has changed, cache is invalid
            
            # Return encoding as numpy array
            enc = cache_data.get('encoding')
            return np.array(enc) if enc is not None else None
        except:
            return None
    
    def load_all_cached_encodings(self, students_data):
        """Load all encodings from cache - returns (encodings, valid_students, missing_students)"""
        encodings = []
        valid_students = []
        missing_students = []
        
        for student_info in students_data:
            rollno = student_info['RollNo']
            name = student_info['Name']
            branch = student_info['Branch']
            img_path = student_info.get('img_path')
            
            encoding = self.load_encoding(rollno, name, branch, img_path)
            if encoding is not None:
                encodings.append(encoding)
                valid_students.append(student_info)
            else:
                missing_students.append(student_info)
        
        return encodings, valid_students, missing_students
    
    def clear_cache(self):
        """Clear all cached encodings"""
        try:
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            return True
        except:
            return False


def batch_encode_and_cache(students_data, cache, batch_size=50):
    """
    Encode students in batches and cache them.
    Returns (encodings, valid_students)
    """
    print(f"Loading {len(students_data)} student encodings...")
    
    # First, load from cache
    cached_encodings, valid_students, missing_students = cache.load_all_cached_encodings(students_data)
    
    print(f"Loaded {len(cached_encodings)} encodings from cache")
    print(f"Missing {len(missing_students)} encodings (will generate now)...")
    
    # Process missing encodings in batches
    for i in range(0, len(missing_students), batch_size):
        batch = missing_students[i:i+batch_size]
        
        for student in batch:
            rollno = student['RollNo']
            name = student['Name']
            branch = student['Branch']
            img_path = student['img_path']
            
            try:
                # Load image
                img = cv2.imread(img_path)
                if img is None:
                    continue
                
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Try fast small model first
                encodes = face_recognition.face_encodings(img_rgb, model="small", num_jitters=1)
                
                if len(encodes) > 0:
                    encoding = encodes[0]
                    # Save to cache
                    cache.save_encoding(rollno, name, branch, encoding, img_path)
                    cached_encodings.append(encoding)
                    valid_students.append(student)
            except Exception as e:
                print(f"Error processing {rollno}: {e}")
        
        progress = min(i + batch_size, len(missing_students))
        print(f"Processed {progress}/{len(missing_students)} new encodings...")
    
    print(f"✓ Total encodings loaded: {len(cached_encodings)}")
    return cached_encodings, valid_students
