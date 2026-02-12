#!/usr/bin/env python3
# cache_manager.py - Utility script to manage face encoding cache

import os
import sys
import json
from pathlib import Path
from face_encoding_cache import FaceEncodingCache
import pickle

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def cache_status():
    """Show current cache status"""
    print_header("CACHE STATUS")
    
    cache = FaceEncodingCache()
    cache_dir = cache.cache_dir
    
    if not os.path.exists(cache_dir):
        print("❌ Cache folder not found")
        return
    
    # Count cache files
    pkl_files = list(Path(cache_dir).glob('*.pkl'))
    print(f"✓ Cache folder: {cache_dir}")
    print(f"✓ Cached encodings: {len(pkl_files)}")
    
    # Calculate cache size
    total_size = sum(f.stat().st_size for f in pkl_files) / (1024*1024)
    print(f"✓ Total cache size: {total_size:.2f} MB")
    
    # Show first few cache files
    if pkl_files:
        print(f"\nFirst 5 cached students:")
        for pkl_file in sorted(pkl_files)[:5]:
            print(f"  - {pkl_file.stem}")

def clear_cache_cmd():
    """Clear all cached encodings"""
    print_header("CLEARING CACHE")
    
    cache = FaceEncodingCache()
    
    if cache.clear_cache():
        print("✓ Cache cleared successfully")
        print("✓ Face encodings will be regenerated on next startup")
    else:
        print("❌ Failed to clear cache")

def rebuild_cache():
    """Rebuild cache by scanning Images_Attendance"""
    print_header("REBUILDING CACHE")
    
    import cv2
    import face_recognition
    import numpy as np
    
    cache = FaceEncodingCache()
    images_path = 'Images_Attendance'
    
    if not os.path.exists(images_path):
        print(f"❌ {images_path} folder not found")
        return
    
    # Collect all students
    students_data = []
    for root_dir, dirs, files in os.walk(images_path):
        for filename in files:
            parts = os.path.splitext(filename)[0].split('_')
            if len(parts) == 3:
                rollno, name, branch = parts
                img_path = os.path.join(root_dir, filename)
                students_data.append({
                    'RollNo': rollno,
                    'Name': name,
                    'Branch': branch,
                    'img_path': img_path
                })
    
    print(f"Found {len(students_data)} students")
    
    # Clear existing cache
    cache.clear_cache()
    print("Cleared existing cache")
    
    # Regenerate encodings
    processed = 0
    for student in students_data:
        try:
            img = cv2.imread(student['img_path'])
            if img is None:
                continue
            
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodes = face_recognition.face_encodings(img_rgb, model="small", num_jitters=1)
            
            if len(encodes) > 0:
                cache.save_encoding(
                    student['RollNo'],
                    student['Name'],
                    student['Branch'],
                    encodes[0],
                    student['img_path']
                )
                processed += 1
                
                if processed % 100 == 0:
                    print(f"  Processed {processed}/{len(students_data)}...")
        except Exception as e:
            print(f"  Error: {student['RollNo']} - {e}")
    
    print(f"✓ Cache rebuilt successfully!")
    print(f"✓ Total encoded: {processed}/{len(students_data)}")

def show_cached_student(rollno):
    """Show details of a cached student"""
    cache = FaceEncodingCache()
    cache_file = os.path.join(cache.cache_dir, f"{rollno}*.pkl")
    
    from glob import glob
    matches = glob(cache_file)
    
    if not matches:
        print(f"❌ Student {rollno} not found in cache")
        return
    
    for match in matches:
        with open(match, 'rb') as f:
            data = pickle.load(f)
        
        print(f"✓ Student: {data['rollno']} - {data['name']} ({data['branch']})")
        print(f"  Cached at: {data['timestamp']}")
        print(f"  File hash: {data['file_hash']}")

def help_menu():
    """Show help menu"""
    print_header("CACHE MANAGER - HELP")
    print("""
Commands:
  status      - Show cache status and size
  clear       - Clear all cached encodings
  rebuild     - Rebuild cache from scratch
  help        - Show this help menu
  
Usage:
  python cache_manager.py status
  python cache_manager.py clear
  python cache_manager.py rebuild
    """)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        help_menu()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        cache_status()
    elif command == "clear":
        response = input("\n⚠️  This will delete all cached encodings. Continue? (y/n): ")
        if response.lower() == 'y':
            clear_cache_cmd()
    elif command == "rebuild":
        response = input("\n⚠️  This will rebuild cache from scratch. Continue? (y/n): ")
        if response.lower() == 'y':
            rebuild_cache()
    elif command == "help":
        help_menu()
    else:
        print(f"❌ Unknown command: {command}")
        help_menu()
